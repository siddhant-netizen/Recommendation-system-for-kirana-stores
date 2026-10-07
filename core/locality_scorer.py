# ─────────────────────────────────────────
# locality_scorer.py — Builds neighborhood
# profile for a kirana store using Apify
# Google Maps reviews. Cached by location.
# ─────────────────────────────────────────
import json
import os
from datetime import date, datetime, timedelta
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_API_KEY = os.getenv("APIFY_API_KEY", "")
CACHE_FILE = "locality_cache.json"
CACHE_DAYS = 7  # Refresh weekly

# Search queries per signal type
SIGNAL_QUERIES = {
    "tourist":       "Homestays lodges trekking",
    "local_food":    "Local restaurants dhabas",
    "office_worker": "Corporate offices IT parks",
    "family":        "Schools playgrounds",
    "budget":        "Budget shops local market",
    "premium":       "Luxury hotels fine dining"
}

# Keywords to look for in reviews
REVIEW_KEYWORDS = {
    "tourist":       ["travel", "trek", "tourist", "sightseeing", "monastery",
                      "hill station", "backpack", "trip", "visit", "explore"],
    "local_food":    ["thukpa", "momos", "authentic", "local", "traditional",
                      "tibetan", "regional", "homemade", "desi", "dhaba"],
    "office_worker": ["office", "corporate", "IT", "tech", "startup",
                      "professional", "business", "coworking"],
    "family":        ["family", "kids", "children", "school", "safe",
                      "playground", "peaceful", "residential"],
    "budget":        ["cheap", "affordable", "budget", "value", "inexpensive",
                      "reasonable", "pocket friendly", "limited"],
    "premium":       ["luxury", "premium", "upscale", "fine", "expensive",
                      "high end", "classy", "sophisticated"]
}

# Maps signals to offer categories for recommendation engine
SIGNAL_TO_OFFER_MAP = {
    "tourist":       ["30% Off All Categories", "Re-engage Bundle", "Free Shipping on Food"],
    "local_food":    ["Free Shipping on Food", "Win Back Deal"],
    "office_worker": ["20% Off Electronics", "10% Cashback on Clothing"],
    "family":        ["Free Shipping on Food", "Win Back Deal", "Re-engage Bundle"],
    "budget":        ["30% Off All Categories", "Win Back Deal"],
    "premium":       ["20% Off Electronics", "10% Cashback on Clothing"]
}

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def is_cache_valid(cached_entry):
    if not cached_entry:
        return False
    cached_date = datetime.strptime(cached_entry["cached_at"], "%Y-%m-%d").date()
    return (date.today() - cached_date).days < CACHE_DAYS

def fetch_reviews_apify(location, queries):
    """Fetch reviews for multiple queries from a location using Apify."""
    client = ApifyClient(APIFY_API_KEY)
    search_strings = [f"{q} in {location}" for q in queries.values()]

    run_input = {
        "searchStringsArray": search_strings,
        "maxCrawledPlacesPerSearch": 2,
        "maxReviews": 5,
        "language": "en",
    }

    print(f"  📡 Fetching reviews from Apify for: {location}")
    run = client.actor("nwua9Gu5YrADL7ZDj").call(run_input=run_input)

    places = []
    for item in client.dataset(run.default_dataset_id).iterate_items():
        places.append(item)
    return places

def extract_signal_scores(places):
    """Extract keyword-based signal scores from review texts."""
    # Collect all review text
    all_text = []
    for place in places:
        reviews = place.get("reviews", [])
        for r in reviews:
            text = r.get("text") or r.get("textTranslated") or ""
            if text:
                all_text.append(text.lower())

    combined_text = " ".join(all_text)
    total_words = len(combined_text.split()) or 1

    scores = {}
    for signal, keywords in REVIEW_KEYWORDS.items():
        mention_count = sum(combined_text.count(kw) for kw in keywords)
        # Normalize by text length — mentions per 100 words
        raw_score = (mention_count / total_words) * 100
        # Cap at 1.0
        scores[signal] = round(min(raw_score * 2, 1.0), 2)

    return scores

def build_neighborhood_profile(location):
    """
    Main function — builds and caches neighborhood
    profile for a kirana store location.
    Returns signal scores dict.
    """
    cache = load_cache()

    # Return cached profile if still valid
    if location in cache and is_cache_valid(cache[location]):
        print(f"  ✅ Using cached profile for {location} (cached {cache[location]['cached_at']})")
        return cache[location]["scores"]

    # Fetch fresh data
    places = fetch_reviews_apify(location, SIGNAL_QUERIES)

    if not places:
        print(f"  ⚠️ No places found for {location} — using neutral profile")
        return {signal: 0.5 for signal in SIGNAL_QUERIES.keys()}

    # Extract scores
    scores = extract_signal_scores(places)

    # Cache the result
    cache[location] = {
        "cached_at": date.today().isoformat(),
        "scores": scores,
        "places_found": len(places)
    }
    save_cache(cache)

    print(f"  ✅ Built profile for {location} ({len(places)} places analysed)")
    return scores

def get_offer_boost(neighborhood_scores, offer_name):
    """
    Returns a locality boost score for a specific offer
    based on the neighborhood profile.
    """
    boosts = []
    for signal, signal_offers in SIGNAL_TO_OFFER_MAP.items():
        if offer_name in signal_offers:
            boosts.append(neighborhood_scores.get(signal, 0))

    return round(sum(boosts) / max(len(boosts), 1), 2) if boosts else 0.0

def adjust_offers_for_locality(base_offer_scores, location):
    """
    Takes base ML offer scores and adjusts them
    based on the store's neighborhood profile.
    Returns re-ranked list of (offer_name, final_score).
    """
    neighborhood_scores = build_neighborhood_profile(location)

    print(f"\n  📊 Neighborhood profile for {location}:")
    for signal, score in sorted(neighborhood_scores.items(), key=lambda x: -x[1]):
        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
        print(f"    {signal:<15} {bar} {score:.2f}")

    adjusted = []
    for offer_name, base_score in base_offer_scores.items():
        boost = get_offer_boost(neighborhood_scores, offer_name)
        # 60% base ML score + 40% locality boost
        final_score = round((base_score * 0.6) + (boost * 0.4), 2)
        adjusted.append((offer_name, base_score, boost, final_score))

    adjusted.sort(key=lambda x: -x[3])
    return adjusted, neighborhood_scores
