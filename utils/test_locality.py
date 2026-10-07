import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, '/home/iddh/recommendation-engine')

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
STORE_LOCATION = "Tawang Arunachal Pradesh"

# ─────────────────────────────────────────
# Step 1 — Fetch neighborhood signals
# around the kirana store's locality
# ─────────────────────────────────────────

NEIGHBORHOOD_QUERIES = {
    "tourist":          "Homestays lodges trekking camps",
    "fitness":          "Gyms fitness studios",
    "office_worker":    "Corporate offices IT parks",
    "family":           "Schools playgrounds",
    "budget":           "Budget hotels cheap eateries",
    "premium":          "Luxury hotels fine dining"
}

REVIEW_KEYWORDS = {
    "tourist":       ["travel", "trek", "tourist", "lodge", "homestay", "sightseeing", "backpack"],
    "fitness":       ["gym", "workout", "protein", "healthy", "fitness", "organic"],
    "office_worker": ["office", "corporate", "IT", "tech", "startup", "professional"],
    "family":        ["family", "kids", "children", "school", "playground", "safe"],
    "budget":        ["cheap", "affordable", "budget", "value", "inexpensive"],
    "premium":       ["luxury", "premium", "upscale", "fine", "expensive", "high-end"]
}

def fetch_places_with_reviews(query, location):
    """Fetch places and their reviews for a locality."""
    search_url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.reviews"
    }
    payload = {
        "textQuery": f"{query} in {location}",
        "maxResultCount": 3
    }
    try:
        res = httpx.post(search_url, json=payload, headers=headers, timeout=15.0)
        if res.status_code == 200:
            return res.json().get("places", [])
        print(f"  API error: {res.status_code}")
        return []
    except Exception as e:
        print(f"  Request failed: {e}")
        return []

def extract_keyword_score(places, keywords):
    """Score how strongly reviews mention relevant keywords."""
    total_mentions = 0
    total_reviews = 0
    for place in places:
        reviews = place.get("reviews", [])
        for review in reviews:
            text = review.get("text", {}).get("text", "").lower()
            total_reviews += 1
            for kw in keywords:
                if kw in text:
                    total_mentions += 1
                    break
    if total_reviews == 0:
        return 0.0
    return round(min(total_mentions / total_reviews, 1.0), 2)

def build_neighborhood_profile(location):
    """Build complete neighborhood profile for a kirana store location."""
    print(f"\n📍 Building neighborhood profile for: {location}\n")
    profile = {}
    for signal, query in NEIGHBORHOOD_QUERIES.items():
        places = fetch_places_with_reviews(query, location)
        keyword_score = extract_keyword_score(places, REVIEW_KEYWORDS[signal])
        place_density = len(places) / 3.0
        # Combined score: 60% place density + 40% review keywords
        combined = round((place_density * 0.6) + (keyword_score * 0.4), 2)
        profile[signal] = combined
        print(f"  {signal:<15} → density: {place_density:.2f} | keywords: {keyword_score:.2f} | combined: {combined:.2f}")
    return profile

def adjust_recommendations_for_locality(base_recommendations, neighborhood_profile):
    """
    Adjust offer recommendations based on neighborhood profile.
    Boosts offers that match the dominant neighborhood signals.
    """
    OFFER_SIGNAL_MAP = {
        "20% Off Electronics":      ["office_worker", "premium"],
        "10% Cashback on Clothing": ["premium", "tourist"],
        "Free Shipping on Food":    ["family", "budget"],
        "Win Back Deal":            ["budget", "family"],
        "Re-engage Bundle":         ["tourist", "fitness"],
        "30% Off All Categories":   ["budget", "tourist"]
    }

    print(f"\n🎯 Adjusting recommendations for {STORE_LOCATION} kirana store:\n")

    scored = []
    for offer_name, base_score in base_recommendations.items():
        signals = OFFER_SIGNAL_MAP.get(offer_name, [])
        locality_boost = sum(neighborhood_profile.get(s, 0) for s in signals) / max(len(signals), 1)
        final_score = round((base_score * 0.6) + (locality_boost * 0.4), 2)
        scored.append((offer_name, base_score, locality_boost, final_score))

    scored.sort(key=lambda x: -x[3])

    print(f"  {'Offer':<30} {'Base':>6} {'Boost':>6} {'Final':>6}")
    print("  " + "-" * 55)
    for offer, base, boost, final in scored:
        print(f"  {offer:<30} {base:>6.2f} {boost:>6.2f} {final:>6.2f}")

    return scored

# ─────────────────────────────────────────
# Run the test
# ─────────────────────────────────────────

# Simulate base ML recommendations (as if all customers were average)
BASE_RECOMMENDATIONS = {
    "20% Off Electronics":      0.50,
    "10% Cashback on Clothing": 0.45,
    "Free Shipping on Food":    0.40,
    "Win Back Deal":            0.35,
    "Re-engage Bundle":         0.30,
    "30% Off All Categories":   0.25
}

print("=" * 60)
print("  Kirana Store Locality-Aware Recommendation Test")
print(f"  Store Location: {STORE_LOCATION}")
print("=" * 60)

# Build neighborhood profile
profile = build_neighborhood_profile(STORE_LOCATION)

# Adjust recommendations
results = adjust_recommendations_for_locality(BASE_RECOMMENDATIONS, profile)

print(f"\n✅ Top 3 recommended offers for {STORE_LOCATION} kirana store:")
for i, (offer, base, boost, final) in enumerate(results[:3], 1):
    print(f"  [{i}] {offer} (score: {final})")
