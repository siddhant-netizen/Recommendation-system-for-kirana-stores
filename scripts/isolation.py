import os
import requests
import json
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TWENTY_API_KEY", "")
BASE_URL = os.getenv("TWENTY_BASE_URL", "http://localhost:3000")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def post(endpoint, payload):
    resp = requests.post(f"{BASE_URL}/rest/{endpoint}", headers=HEADERS, json=payload)
    return resp

def patch(endpoint, record_id, payload):
    resp = requests.patch(f"{BASE_URL}/rest/{endpoint}/{record_id}", headers=HEADERS, json=payload)
    return resp

results = {}

# ── Step 1: Create Customer ─────────────────────────
print("\n[1] Creating customer...")
resp = post("customers", {
    "firstName": "Test",
    "lastName": "User",
    "age": 28,
    "gender": "MALE",
    "city": "Mumbai",
    "email": {"primaryEmail": "test.isolate@test.com"},
    "phone": {
        "primaryPhoneNumber": "9999999999",
        "primaryPhoneCountryCode": "IN",
        "primaryPhoneCallingCode": "+91"
    }
})
if resp.ok:
    results["customer_id"] = resp.json().get("data", {}).get("createCustomer", {}).get("id")
    print(f"  ✅ Customer created: {results['customer_id']}")
else:
    print(f"  ❌ Failed: {resp.text}")
    exit()

# ── Step 2: Create Purchase ─────────────────────────
print("\n[2] Creating purchase...")
resp = post("purchases", {
    "customerId": results["customer_id"],
    "activityType": "PURCHASE",
    "category": "ELECTRONICS",
    "amount": 2500,
    "channel": "APP",
    "activityDate": (date.today() - timedelta(days=5)).isoformat() + "T00:00:00.000Z"
})
if resp.ok:
    results["purchase_id"] = resp.json().get("data", {}).get("createPurchase", {}).get("id")
    print(f"  ✅ Purchase created: {results['purchase_id']}")
else:
    print(f"  ❌ Failed: {resp.text}")

# ── Step 3: Create Offer ────────────────────────────
print("\n[3] Creating offer...")
resp = post("offers", {
    "name": "Test Offer",
    "offerType": "DISCOUNT",
    "discountPercentage": 20,
    "applicablecategory": "ELECTRONICS",
    "minimumOrderValue": 500,
    "targetSegment": "VIP",
    "expiryDate": (date.today() + timedelta(days=30)).isoformat() + "T00:00:00.000Z",
    "isActive": True
})
if resp.ok:
    results["offer_id"] = resp.json().get("data", {}).get("createOffer", {}).get("id")
    print(f"  ✅ Offer created: {results['offer_id']}")
else:
    print(f"  ❌ Failed: {resp.text}")
    exit()

# ── Step 4: Create Customer Group ───────────────────
print("\n[4] Creating customer group...")
resp = post("customerGroups", {
    "name": "VIP",
    "groupName": "VIP",
    "rfmSegment": "VIP",
    "size": 1,
    "avgspend": 2500.0,
    "avgpurchasefrequency": 3.0,
    "dominantCategory": "ELECTRONICS"
})
if resp.ok:
    data = resp.json().get("data", {})
    results["group_id"] = (
        data.get("id") or
        data.get("createCustomerGroup", {}).get("id")
    )
    print(f"  ✅ Group created: {results['group_id']}")
else:
    print(f"  ❌ Failed: {resp.text}")

# ── Step 5: Link Customer to Group ──────────────────
print("\n[5] Linking customer to group...")
if results.get("group_id"):
    resp = patch("customers", results["customer_id"], {
        "customerGroupsId": results["group_id"]
    })
    if resp.ok:
        print(f"  ✅ Customer linked to group")
    else:
        print(f"  ❌ Failed: {resp.text}")
        # Try connect syntax if direct ID fails
        print("  Trying connect syntax...")
        resp = patch("customers", results["customer_id"], {
            "customerGroups": {
                "connect": {"id": results["group_id"]}
            }
        })
        if resp.ok:
            print(f"  ✅ Linked via connect syntax")
        else:
            print(f"  ❌ Connect also failed: {resp.text}")

# ── Step 6: Create Customer Offer ───────────────────
print("\n[6] Creating customer offer...")
if results.get("customer_id") and results.get("offer_id"):
    resp = post("customeroffers", {
        "customersId": results["customer_id"],
        "offerId": results["offer_id"],
        "rfmSegment": "VIP",
        "confidenceScore": 0.93,
        "status": "PENDING",
        "deliveryStatus": "PENDING",
        "recommendedAt": date.today().isoformat()
    })
    if resp.ok:
        results["customer_offer_id"] = resp.json().get("data", {}).get("createCustomeroffer", {}).get("id")
        print(f"  ✅ Customer offer created: {results['customer_offer_id']}")
    else:
        print(f"  ❌ Failed: {resp.text}")

# ── Summary ──────────────────────────────────────────
print("\n" + "="*50)
print("ISOLATION TEST SUMMARY")
print("="*50)
for key, val in results.items():
    print(f"  {key}: {val}")
