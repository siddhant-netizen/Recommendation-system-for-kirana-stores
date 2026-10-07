import os
import requests
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TWENTY_API_KEY", "")
BASE_URL = os.getenv("TWENTY_BASE_URL", "http://localhost:3000")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

offers = [
    {
        "name": "20% Off Electronics",
        "offerType": "DISCOUNT",
        "discountPercentage": 20,
        "applicablecategory": "ELECTRONICS",
        "minimumOrderValue": 500,
        "targetSegment": "VIP",
        "expiryDate": (date.today() + timedelta(days=30)).isoformat() + "T00:00:00.000Z",
        "isActive": True
    },
    {
        "name": "10% Cashback on Clothing",
        "offerType": "CASHBACK",
        "discountPercentage": 10,
        "applicablecategory": "CLOTHING",
        "minimumOrderValue": 300,
        "targetSegment": "LOYAL",
        "expiryDate": (date.today() + timedelta(days=30)).isoformat() + "T00:00:00.000Z",
        "isActive": True
    },
    {
        "name": "Free Shipping on Food",
        "offerType": "FREE_SHIPPING",
        "discountPercentage": 0,
        "applicablecategory": "FOOD",
        "minimumOrderValue": 200,
        "targetSegment": "NEW",
        "expiryDate": (date.today() + timedelta(days=30)).isoformat() + "T00:00:00.000Z",
        "isActive": True
    },
    {
        "name": "Win Back Deal",
        "offerType": "DISCOUNT",
        "discountPercentage": 25,
        "applicablecategory": "ELECTRONICS",
        "minimumOrderValue": 500,
        "targetSegment": "AT_RISK",
        "expiryDate": (date.today() + timedelta(days=30)).isoformat() + "T00:00:00.000Z",
        "isActive": True
    },
    {
        "name": "Re-engage Bundle",
        "offerType": "BUNDLE",
        "discountPercentage": 15,
        "applicablecategory": "CLOTHING",
        "minimumOrderValue": 300,
        "targetSegment": "AT_RISK",
        "expiryDate": (date.today() + timedelta(days=30)).isoformat() + "T00:00:00.000Z",
        "isActive": True
    },
    {
        "name": "30% Off All Categories",
        "offerType": "DISCOUNT",
        "discountPercentage": 30,
        "applicablecategory": "ELECTRONICS",
        "minimumOrderValue": 100,
        "targetSegment": "DORMANT",
        "expiryDate": (date.today() + timedelta(days=30)).isoformat() + "T00:00:00.000Z",
        "isActive": True
    },
]

print("Populating offers...\n")

for offer in offers:
    resp = requests.post(f"{BASE_URL}/rest/offers", headers=HEADERS, json=offer)
    if resp.ok:
        print(f"✅ Created: {offer['name']}")
    else:
        print(f"❌ Failed: {offer['name']} → {resp.text}")

print("\nDone!")
