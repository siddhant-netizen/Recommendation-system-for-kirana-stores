import os
import httpx
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

url = "https://places.googleapis.com/v1/places:searchText"
headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": GOOGLE_API_KEY,
    "X-Goog-FieldMask": "places.id,places.displayName,places.reviews,places.editorialSummary"
}
payload = {
    "textQuery": "Homestays in Tawang Arunachal Pradesh",
    "maxResultCount": 3
}

res = httpx.post(url, json=payload, headers=headers, timeout=15.0)
import json
print(json.dumps(res.json(), indent=2))
