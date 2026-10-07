# ─────────────────────────────────────────
# offer_generator.py — Behavior Drift Logic
# ─────────────────────────────────────────
import json
import os
from datetime import date, timedelta
from core.data_fetcher import create_record

# Expanded matrix to cover all downward drift transitions
OFFER_TEMPLATES = {
    "VIP_to_Loyal": {"name": "Loyalty Retention", "offer_type": "DISCOUNT", "discount_percentage": 15, "minimum_order_value": 1000, "target_segment": "Loyal"},
    "VIP_to_At Risk": {"name": "VIP Urgent Intervention", "offer_type": "CASHBACK", "discount_percentage": 25, "minimum_order_value": 800, "target_segment": "At Risk"},
    "VIP_to_Dormant": {"name": "Massive VIP Win-Back", "offer_type": "DISCOUNT", "discount_percentage": 40, "minimum_order_value": 500, "target_segment": "Dormant"},
    "Loyal_to_At Risk": {"name": "Win Back Offer", "offer_type": "CASHBACK", "discount_percentage": 20, "minimum_order_value": 500, "target_segment": "At Risk"},
    "Loyal_to_Dormant": {"name": "Loyal Reactivation", "offer_type": "DISCOUNT", "discount_percentage": 30, "minimum_order_value": 300, "target_segment": "Dormant"},
    "At Risk_to_Dormant": {"name": "Re-engagement Offer", "offer_type": "DISCOUNT", "discount_percentage": 30, "minimum_order_value": 200, "target_segment": "Dormant"},
    "New_to_Dormant": {"name": "Second Chance Welcome", "offer_type": "FREE_SHIPPING", "discount_percentage": 0, "minimum_order_value": 100, "target_segment": "Dormant"},
    "default": {"name": "Special Recovery Offer", "offer_type": "DISCOUNT", "discount_percentage": 25, "minimum_order_value": 300, "target_segment": "At Risk"}
}

CATEGORY_REVERSE = {
    0: "Electronics", 1: "Clothing",
    2: "Food", 3: "Beauty", 4: "Sports"
}

def get_offer_template(previous_segment, current_segment):
    """Returns the right offer template based on segment transition."""
    key = f"{previous_segment}_to_{current_segment}"
    return OFFER_TEMPLATES.get(key, OFFER_TEMPLATES["default"])

def create_offer_in_twenty(template, category, reason="Behavior drift detected"):
    """Creates a new offer record in Twenty CRM."""
    expiry = (date.today() + timedelta(days=7)).isoformat()
    safe_category = category.upper()
    safe_segment = template["target_segment"].upper().replace(" ", "_")
    # Mapped PERFECTLY to your provided Twenty CRM schema fields
    payload = {
        "name": template["name"],                  # Lowercase 'n'
        "offerType": template["offer_type"],       # CamelCase
        "discountPercentage": template["discount_percentage"], # CamelCase
        "minimumOrderValue": template["minimum_order_value"],  # CamelCase
        "applicableCategory": safe_category,            # CamelCase
        "targetSegment": safe_segment, # CamelCase
        "expiryDate": expiry + "T00:00:00.000Z",   # CamelCase
        "isActive": True                           # CamelCase
    }
    
    print(f"  DEBUG payload: {payload}")
    resp = create_record("offers", payload)
    
    if resp is not None and resp.ok:
        offer_data = resp.json().get("data", {})
        offer_id = offer_data.get("id") or offer_data.get("createOffer", {}).get("id")
        print(f"  ✅ Created offer: {template['name']} (id: {offer_id})")
        return offer_id
    else:
        # This will now correctly print the 400 or 422 error code!
        status = resp.status_code if resp is not None else 'No response'
        print(f"  ❌ Failed to create offer: {status}")
        
        # This will print the EXACT reason Twenty CRM is rejecting it
        if resp is not None:
            print(f"  ❌ Error details: {resp.text}") 
        return None

def run_offer_generation(df, cache=None):
    """
    Main function — runs drift detection and generates
    offers for customers with significant behavior drops.
    """
    print("\n🔍 Running Offer Generation (Drift Detection)...\n")

    snapshot = load_snapshot()
    
    # 🐛 FIXED: Prevented double-saving. If no snapshot, exit cleanly.
    if not snapshot:
        print("  No previous snapshot found — baseline will be saved at the end of the engine run.")
        return []

    generated_offers = []
    affected_segments = {}

    for _, row in df.iterrows():
        customer_id = str(row["customer_id"])
        previous = snapshot.get(customer_id)

        if not previous:
            print("previous issue")
            continue

        has_drift = detect_behavior_drift(row, previous)
        print(f"has drift is {has_drift}")
        if has_drift:
            prev_segment = previous.get("segment", "Unknown")
            curr_segment = row["segment"]
            category = CATEGORY_REVERSE.get(int(row["dominant_category"]), "Electronics")

            print(f"  ⚠️ Drift detected: {row['name']} | {prev_segment} → {curr_segment}")

            transition_key = f"{prev_segment}_to_{curr_segment}"
            if transition_key not in affected_segments:
                template = get_offer_template(prev_segment, curr_segment)
                offer_id = create_offer_in_twenty(template, category)
                
                if offer_id:
                    affected_segments[transition_key] = offer_id
                    generated_offers.append({
                        "offer_id": offer_id,
                        "transition": transition_key,
                        "template": template
                    })

    # REMOVED: save_snapshot(df) is no longer called here.
    print(f"\n✅ Offer generation complete — {len(generated_offers)} new offers created")
    return generated_offers

SNAPSHOT_FILE = "rfm_snapshot.json"

def load_snapshot():
    if os.path.exists(SNAPSHOT_FILE):
        with open(SNAPSHOT_FILE, "r") as f:
            return json.load(f)
    return {}

def save_snapshot(df):
    """Saves today's metrics. Now ONLY called by engine.py."""
    snapshot = {}
    segment_map = {"VIP": 5, "Loyal": 4, "At Risk": 3, "New": 2, "Dormant": 1}

    for _, row in df.iterrows():
        customer_id = str(row["customer_id"])
        snapshot[customer_id] = {
            "segment": row["segment"],
            "rfm_score": segment_map.get(row["segment"], 1),
            "recency_days": row["recency_days"],
            "monetary": row["monetary"]
        }

    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(snapshot, f, indent=4)
    print(f"📸 Saved daily snapshot for {len(snapshot)} customers.")

def detect_behavior_drift(current_row, previous_data):
    """
    Calculates drift score.
    Returns True ONLY if engagement drops severely (Score >= 4).
    """
    if not previous_data:
        return False

    segment_map = {"VIP": 5, "Loyal": 4, "At Risk": 3, "New": 2, "Dormant": 1}
    current_rfm = segment_map.get(current_row["segment"], 1)
    previous_rfm = previous_data.get("rfm_score", 1)

    # 🐛 THE FIX: Only block if they actually IMPROVED tiers. 
    # If they stayed in the same tier (==), we still need to check for recency/spend drops!
    if current_rfm > previous_rfm:
        return False

    drift_score = 0

    # 1. Dynamic Segment Drop (+2 per tier dropped)
    # If they stayed in the same tier, drop_magnitude is 0 (no points added).
    drop_magnitude = previous_rfm - current_rfm
    drift_score += (drop_magnitude * 2) 

    # 2. Recency Spike (+2)
    # Did they go silent for 14+ days since the last snapshot?
    if current_row["recency_days"] - previous_data.get("recency_days", 0) >= 14:
        drift_score += 2

    # 3. Spend Drop (+2) 
    # 🐛 THE FIX: Require a meaningful drop (e.g., a 10% decrease in spend), not just a $1 difference.
    previous_spend = previous_data.get("monetary", 0)
    if previous_spend > 0 and current_row["monetary"] <= (previous_spend * 0.90):
        drift_score += 2

    return drift_score >= 4
