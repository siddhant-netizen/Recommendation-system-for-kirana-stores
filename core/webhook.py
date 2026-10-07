import requests
from core.config import WEBHOOK_URL_SINGLE, WEBHOOK_URL_GROUP

def fire_single_webhook(customer, offer, segment, confidence):
    """
    Fires a webhook for a single customer recommendation.
    """
    payload = {
        "type": "single",
        "customer": {
            "name": customer.get("name", ""),
            "email": customer.get("email", ""),
            "phone": customer.get("phone", ""),
            "segment": segment,
            "confidence": confidence
        },
        "offer": {
            "offer_name": offer.get("name", ""),
            "offer_type": offer.get("offerType", ""),
            "discount": offer.get("discountPercentage", 0)
        }
    }

    try:
        response = requests.post(WEBHOOK_URL_SINGLE, json=payload)
        print(f"  📤 Single webhook → HTTP {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"  ❌ Single webhook failed: {e}")
        return None

def fire_group_webhook(customers_data, offer):
    """
    Fires a webhook for a group of 2+ customers
    sharing the same recommended offer.
    """
    payload = {
        "type": "group",
        "offer": {
            "offer_name": offer.get("name", ""),
            "offer_type": offer.get("offerType", ""),
            "discount": offer.get("discountPercentage", 0)
        },
        "group_size": len(customers_data),
        "customers": customers_data
    }

    try:
        response = requests.post(WEBHOOK_URL_GROUP, json=payload)
        print(f"  📤 Group webhook ({len(customers_data)} customers) → HTTP {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"  ❌ Group webhook failed: {e}")
        return None

def fire_webhooks(offer_groups):
    """
    Orchestrates webhook firing:
    - Single webhook for each individual customer
    - Group webhook for offers with 2+ customers
    """
    print("\nFiring webhooks...\n")

    for offer_id, group in offer_groups.items():
        offer = group[0]["offer"]
        print(f"Offer: {offer.get('name')} → {len(group)} customer(s)")

        # Always fire single webhook per customer
        for c in group:
            fire_single_webhook(
                {"name": c["name"], "email": c["email"], "phone": c["phone"]},
                offer,
                c["segment"],
                c["confidence"]
            )

        # Fire group webhook only if 2+ customers
        if len(group) >= 2:
            customers_data = [
                {
                    "name": c["name"],
                    "email": c["email"],
                    "phone": c["phone"],
                    "segment": c["segment"],
                    "confidence": c["confidence"]
                }
                for c in group
            ]
            fire_group_webhook(customers_data, offer)

        print()
