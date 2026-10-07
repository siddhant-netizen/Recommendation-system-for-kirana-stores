# ─────────────────────────────────────────
# populate_test.py — Injects 5 Test Users
# ─────────────────────────────────────────
import os
import requests
import time
from datetime import date, timedelta
import random
from dotenv import load_dotenv

load_dotenv()

# Ensure these match your core/config.py
API_KEY = os.getenv("TWENTY_API_KEY", "")
BASE_URL = os.getenv("TWENTY_BASE_URL", "http://localhost:3000")

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
})

# 1. Test Customers Data
test_customers = [
    {
        "name": "Akshat", "lastName": "Jain", "email": {"primaryEmail": "akshat@test.com"},
        "mobileOs": "Android", "deviceModel": "OnePlus Nord", "primaryCountry": "India",
        "city": "Nagpur", "gender": "MALE",
        "behavioralTags": ["high_value_adventure_travelers", "tech_affinity"],
        "mlFeatureVector": {"propensity_score": 0.95, "channel_pref": "email"}
    },
    {
        "name": "Siddhant", "lastName": "Dakhore", "email": {"primaryEmail": "siddhant@test.com"},
        "mobileOs": "iOS", "deviceModel": "iPhone 15", "primaryCountry": "India",
        "city": "Pune", "gender": "MALE",
        "behavioralTags": ["sustainability_conscious"],
        "mlFeatureVector": {"propensity_score": 0.88, "channel_pref": "sms"}
    },
    {
        "name": "Arjun", "lastName": "Patel", "email": {"primaryEmail": "arjun@test.com"},
        "mobileOs": "Android", "deviceModel": "Samsung S23", "primaryCountry": "India",
        "city": "Mumbai", "gender": "MALE",
        "behavioralTags": ["deal_seeker"],
        "mlFeatureVector": {"propensity_score": 0.45, "channel_pref": "email"}
    },
    {
        "name": "Neha", "lastName": "Sharma", "email": {"primaryEmail": "neha@test.com"},
        "mobileOs": "iOS", "deviceModel": "iPhone 13", "primaryCountry": "India",
        "city": "Delhi", "gender": "FEMALE",
        "behavioralTags": ["high_social_engagement"],
        "mlFeatureVector": {"propensity_score": 0.75, "channel_pref": "whatsapp"}
    },
    {
        "name": "Rahul", "lastName": "Verma", "email": {"primaryEmail": "rahul@test.com"},
        "mobileOs": "Android", "deviceModel": "Pixel 7", "primaryCountry": "India",
        "city": "Bangalore", "gender": "MALE",
        "behavioralTags": ["dormant_user"],
        "mlFeatureVector": {"propensity_score": 0.12, "channel_pref": "email"}
    }
]

print("🚀 Injecting 5 Test Customers into Twenty CRM...")
customer_ids = []

for c in test_customers:
    resp = session.post(f"{BASE_URL}/rest/customers", json=c)
    if resp.ok:
        payload = resp.json()
        data_block = payload.get("data", {})
        
        # Hunt for the ID in the nested GraphQL response
        new_id = data_block.get("id") or data_block.get("createCustomer", {}).get("id")
        
        # Ultimate fallback: check any dictionary inside 'data' for an 'id'
        if not new_id:
            for key, val in data_block.items():
                if isinstance(val, dict) and "id" in val:
                    new_id = val.get("id")
                    break
        
        if new_id:
            customer_ids.append(new_id)
            print(f"  ✅ Created {c['name']} {c['lastName']} (ID: {new_id[:8]}...)")
        else:
            print(f"  ⚠️ Created {c['name']}, but couldn't parse ID. Raw payload: {payload}")
    else:
        print(f"  ❌ Failed to create {c['name']}: {resp.text}")
    time.sleep(0.5)
# 2. Inject Telemetry & Purchases
print("\n🛒 Injecting Telemetry & Purchases...")

# FIXED: Removed SPORTS and BEAUTY to match your CRM's exact allowed categories
categories = ["ELECTRONICS", "CLOTHING", "FOOD"]

for idx, cid in enumerate(customer_ids):
    if not cid: continue
    
    days_ago = random.randint(1, 5) if idx < 2 else random.randint(40, 100)
    
    for _ in range(3):
        # FIXED: Changed to EXACT uppercase matches for Twenty CRM API
        activity_type = random.choice(["PURCHASE", "BROWSE", "CART_ABANDON"])
        
        payload = {
            "name": f"{activity_type} - {random.choice(categories).title()}",
            "customerId": cid,
            "activityType": activity_type,
            "category": random.choice(categories),
            "amount": random.randint(500, 5000) if activity_type == "PURCHASE" else 0,
            "activityDate": (date.today() - timedelta(days=days_ago)).isoformat() + "T12:00:00Z",
            "sourceDomain": "test.com",
            "rawPayload": {"ip": f"103.241.12.{random.randint(10,99)}", "user_agent": "Mozilla/5.0"}
        }
        
        resp = session.post(f"{BASE_URL}/rest/purchases", json=payload)
        if resp.ok:
            print(f"  ✅ Logged {activity_type} for customer {cid[:8]}...")
        else:
            print(f"  ❌ Purchase Error: {resp.text}")
        time.sleep(0.5)

print("\n✅ Database populated and ready for ML Engine test!")
