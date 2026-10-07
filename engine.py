import time
from datetime import date,timedelta
from core.locality_scorer import adjust_offers_for_locality, build_neighborhood_profile
from collections import defaultdict
from core.data_fetcher import session, BASE_URL
from core.config import SEGMENT_API_MAP
from core.data_fetcher import (
    get_customers,
    get_purchases,
    get_offers,
    get_customer_offers,
    create_record,
)
from core.feature_engineer import build_customer_features
from core.segmentation import segment_customers
from core.recommender import train_offer_matcher, predict_offer, get_offer_feature_importance
from core.group_sync import sync_customer_groups, link_customer_to_group
from core.webhook import fire_webhooks
from core.offer_generator import load_snapshot, save_snapshot, detect_behavior_drift, run_offer_generation
# Add this near your existing imports
from context_fetcher import get_store_weather, get_store_cultural_context
from core.ai_marketer import generate_autonomous_context_offer

# Add these hardcoded configuration variables
STORE_METADATA = {
    "lat": 19.0760,       # Mumbai coordinates for testing
    "lon": 72.8777,
    "country": "IN",
    "state": "in-mh"      # Maharashtra regional code
}
import os
from dotenv import load_dotenv

load_dotenv()

# Replace this with your actual key from calendarific.com when ready
CALENDARIFIC_API_KEY = os.getenv("CALENDARIFIC_API_KEY", "")


def create_offer_in_twenty(template, category):
    """Creates a standalone contextual offer record inside Twenty CRM."""
    expiry = (date.today() + timedelta(days=7)).isoformat() if 'timedelta' in globals() else date.today().isoformat()

    # Force strict uppercase conversions for database Enum compatibility
    safe_category = category.upper()
    safe_segment = template["targetSegment"].upper().replace(" ", "_")

    payload = {
        "name": template["name"],
        "offerType": template["offerType"].upper(),
        "discountPercentage": template["discountPercentage"],
        "minimumOrderValue": template["minimumOrderValue"],
        "applicableCategory": safe_category,   # e.g., "FOOD"
        "targetSegment": safe_segment,         # e.g., "ALL_CUSTOMERS"
        "expiryDate": expiry + "T00:00:00.000Z",
        "isActive": True
    }

    print(f"    [Context API] Posting payload: {payload}")
    resp = create_record("offers", payload)

    if resp is not None and resp.ok:
        offer_data = resp.json().get("data", {})
        offer_id = offer_data.get("id") or offer_data.get("createOffer", {}).get("id")
        print(f"    ✅ Context Offer Created Successfully! (id: {offer_id})")
        return offer_id
    else:
        status = resp.status_code if resp is not None else 'No response'
        print(f"    ❌ Context Offer Post Failed: {status}")
        if resp is not None:
            print(f"    ❌ Error Details: {resp.text}")
        return None


def save_customer_offer(cache, customer_id, offer_id, segment, confidence):
    """
    Saves a recommendation to Twenty CRM.
    Skips if already exists using cache.
    """
    key = (str(customer_id), str(offer_id))
    if key in cache:
        return "SKIPPED"

    payload = {
        "customersId": str(customer_id),
        "offerId": str(offer_id),
        "rfmSegment": SEGMENT_API_MAP.get(segment, "NEW"),
        "confidenceScore": confidence,
        "status": "PENDING",
        "recommendedAt": date.today().isoformat()
    }

    resp = create_record("customeroffers", payload)

    # Safely handle the response object
    if resp and resp.ok:
        cache.add(key)
        return "SAVED"

    status_code = resp.status_code if resp else "TIMEOUT/FAIL"
    return f"ERROR {status_code}"

def run():
    print("=" * 50)
    print("  ML Recommendation Engine")
    print(f"  {date.today()}")
    print("=" * 50)
    start_time = time.time()

    # ── Step 1: Fetch Data ──────────────────────
    print("\n📦 Fetching data from Twenty CRM...")
    customers = get_customers()
    purchases = get_purchases()
    offers = get_offers()

    if not customers:
        print("❌ No customers found. Exiting.")
        return
    if not offers:
        print("❌ No offers found. Exiting.")
        return

    print(f"✅ {len(customers)} customers, {len(purchases)} purchases, {len(offers)} offers")
    # ── Locality Profile ────────────────────
    STORE_LOCATION = "Tawang Arunachal Pradesh"
    print(f"\n📍 Loading locality profile for: {STORE_LOCATION}...")
    base_offer_scores = {o.get("name", ""): 0.5 for o in offers}
    adjusted_offers, neighborhood_scores = adjust_offers_for_locality(
        base_offer_scores, STORE_LOCATION
    )
    locality_boost_map = {name: final for name, base, boost, final in adjusted_offers}
    print(f"✅ Locality profile loaded")
    # ── Step 2: Build Features ──────────────────
    print("\n🔧 Building customer features...")
    df = build_customer_features(customers, purchases)
    print(f"✅ Features built for {len(df)} customers")

    # ── Step 3: Segment Customers ───────────────
    print("\n🎯 Segmenting customers...")
    df = segment_customers(df)

    # ── Step 4: Sync Groups to Twenty ──────────
    group_id_mapping = sync_customer_groups(df)
    
    # ── Step 5: Build duplicate cache ──────────
    print("\n🔍 Building recommendation cache...")
    existing = get_customer_offers()
    cache = {
        (str(m.get("customerId")), str(m.get("offerId")))
        for m in existing
        if m.get("customerId")
    }
    print(f"✅ {len(cache)} existing recommendations cached")

    # ── Step 5.5: Generate Offers from Drift ───
    new_offers = run_offer_generation(df, cache)
    if new_offers:
        offers = get_offers()  # refresh offers catalog
        print(f"  📦 Offers catalog refreshed: {len(offers)} total")

    # ── Step 6: Train ML Model ──────────────────
    print("\n🤖 Training Random Forest...")
    rf = train_offer_matcher(offers)

    # Print feature importance
    importance = get_offer_feature_importance(rf, offers)
    print("\nFeature Importance:")
    for feat, imp in sorted(importance.items(), key=lambda x: -x[1]):
        print(f"  {feat}: {imp}")

    # ── Step 7: Generate Recommendations ───────
    print("\n💡 Generating recommendations...\n")
    offer_groups = defaultdict(list)
    segment_map = {"VIP": 4, "Loyal": 3, "At Risk": 2, "New": 1, "Dormant": 0}
    # ─── INJECT THIS INSTEAD OF THE OLD LOOPS FIRST ───
    print("🔍 Running Offer Generation (Drift Detection)...")

    # 1. Fetch our new independent environmental inputs
    weather_signal = get_store_weather(STORE_METADATA["lat"], STORE_METADATA["lon"])
    cultural_signal = get_store_cultural_context(CALENDARIFIC_API_KEY, STORE_METADATA["country"], STORE_METADATA["state"])
    print(weather_signal,cultural_signal)
    weather_signal = "HOT_SUMMER"
    cultural_signal = "HOLI"
    # 2. Check
    ai_offer_template = generate_autonomous_context_offer(weather_signal, cultural_signal)

    if ai_offer_template:
        print(f"    ✨ AI Strategist Output: \"{ai_offer_template['name']}\"")
        new_offer_id = create_offer_in_twenty(ai_offer_template, ai_offer_template["applicableCategory"])
        if new_offer_id:
            # Re-fetch offers cache so the newly generated option immediately participates in the ML loop!
            offers = get_offers()
            print(f"    📦 Offers database catalog synchronized: {len(offers)} total offers")

# 3. Your Existing Paradigm 1 (Individual Customer Drift Loop) Runs Below:
# (Leave your existing 'for customer in customers:' behavior drift loop intact right here)
    # 1. Load Yesterday's Snapshot for Trigger A
    past_snapshots = load_snapshot()

    for _, row in df.iterrows():
        customer_id = str(row["customer_id"])
        past_metrics = past_snapshots.get(customer_id, {})

        # 2. Check for Trigger A (Behavior Drift)
        is_drifting = detect_behavior_drift(row, past_metrics)

        if is_drifting:
            print(f"  🚨 DRIFT DETECTED: {row['name']} dropped engagement. Triggering Win-Back.")

            # Override ML: Force a re-engagement match by grabbing an "At Risk" offer
            fallback_offer = next((o for o in offers if o.get("targetSegment") in ["At Risk", "Dormant"]), offers[0])
            offer = fallback_offer
            confidence = 0.99  # Forced high confidence for critical trigger
            reason = "Trigger A: Severe behavior drift detected (RFM/Spend Drop)."

        else:
            # Standard ML Match
            offer, confidence_int = predict_offer(rf, row, offers)

            # Ensure confidence is a float for n8n router
            base_confidence = round(float(confidence_int) / 100.0, 2)
            locality_boost = locality_boost_map.get(offer.get("name", ""), 0.5)
            confidence = round((base_confidence * 0.6) + (locality_boost * 0.4), 2)
            reason = "ML Engine: Standard telemetry feature match."

        if not offer:
            continue

        o_id = str(offer.get("id"))

        # Fast O(1) cache check
        if (customer_id, o_id) in cache:
            status = "SKIPPED"
        else:
            # 1. FIXED: camelCase for recommendationReason and deliveryStatus
            # Also using "PENDING" in all-caps just to be safe with Enums
            payload = {
                "customersId": customer_id,
                "offerId": o_id,
                "rfmSegment": row["segment"].upper().replace(" ", "_"),
                "confidenceScore": confidence,
                "recommendationReason": reason,
                "deliveryStatus": "PENDING",
                "status": "PENDING",
                "recommendedAt": date.today().isoformat()
            }

            resp = session.post(f"{BASE_URL}/rest/customeroffers", json=payload)
            if resp.status_code == 429:
                time.sleep(61)
                resp = session.post(f"{BASE_URL}/rest/customeroffers", json=payload)
            status = "SAVED" if resp.ok else f"ERROR {resp.status_code} - {resp.text}"
            
            # Add to cache if successful so we don't duplicate on re-runs
            if resp.ok:
                cache.add((customer_id, o_id))

        if not is_drifting:
            print(f"  ✅ {row['name']:<20} ({row['segment']}) → {offer.get('name', ''):<30} [{confidence}] → {status}")
        
        # Link customer to their group
        group_id = group_id_mapping.get(row["segment"])
        #print(f"    DEBUG: segment={row['segment']} group_id={group_id} mapping={group_id_mapping}")
        if group_id:
           link_customer_to_group(customer_id, group_id)
           
        # 2. FIXED: Added 'phone' safely using .get() to prevent the KeyError
        offer_groups[o_id].append({
            "name": row["name"],
            "email": row["email"],
            "phone": row.get("phone", ""),
            "segment": row["segment"],
            "confidence": confidence,
            "offer": offer
        })

    # ── Step 8: Save Today's Snapshot ──────────
    print("\n💾 Updating behavior drift snapshots...")
    save_snapshot(df)

    fire_webhooks(offer_groups)

    # ── Done ────────────────────────────────────
    elapsed = round(time.time() - start_time, 2)
    print("=" * 50)
    print(f"✅ Engine run complete in {elapsed}s")
    print("=" * 50)

if __name__ == "__main__":
    run()
