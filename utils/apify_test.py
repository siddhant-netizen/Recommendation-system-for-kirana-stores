import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, '/home/iddh/recommendation-engine')
from apify_client import ApifyClient

APIFY_API_KEY = os.getenv("APIFY_API_KEY", "")
STORE_LOCATION = "Tawang, Arunachal Pradesh, India"

client = ApifyClient(APIFY_API_KEY)

print(f"🔍 Fetching Google Maps reviews for: {STORE_LOCATION}\n")

# Run the Google Maps Reviews Scraper actor
run_input = {
    "searchStringsArray": [
        f"Homestays in {STORE_LOCATION}",
        f"Restaurants in {STORE_LOCATION}",
        f"Shops in {STORE_LOCATION}"
    ],
    "maxCrawledPlacesPerSearch": 2,
    "maxReviews": 5,
    "language": "en",
    "exportPlaceUrls": False
}

print("⏳ Running Apify actor...")
run = client.actor("nwua9Gu5YrADL7ZDj").call(run_input=run_input)

print("✅ Done! Fetching results...\n")
results = []
for item in client.dataset(run.default_dataset_id).iterate_items():
    results.append(item)
    print(f"📍 {item.get('title')}")
    print(f"   Category: {item.get('categoryName')}")
    print(f"   Rating: {item.get('totalScore')}")
    reviews = item.get("reviews", [])
    print(f"   Reviews ({len(reviews)}):")
    if reviews:
        print(f"   Review fields available: {list(reviews[0].keys())}")
    for r in reviews[:5]:
        text = r.get('text') or r.get('textTranslated') or ''
        if text:
           print(f"     → {text[:150]}")
        else:
           print(f"     → [No text]")
    print()

print(f"Total places fetched: {len(results)}")
