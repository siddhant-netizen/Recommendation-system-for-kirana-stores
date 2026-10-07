import pandas as pd
from datetime import datetime, date
from core.config import CATEGORY_MAP

def build_customer_features(customers, purchases):
    """
    Transforms raw customer + purchase data into
    a feature matrix ready for ML models.
    """
    features = []

    for customer in customers:
        customer_id = customer.get("id")
        if not customer_id:
            continue

        # Split activities by type
        all_activities = [
            p for p in purchases
            if p.get("customerId") == customer_id
        ]
        customer_purchases = [
            p for p in all_activities
            if p.get("activityType") == "PURCHASE"
        ]
        browse_count = len([
            p for p in all_activities
            if p.get("activityType") == "BROWSE"
        ])
        cart_abandon_count = len([
            p for p in all_activities
            if p.get("activityType") == "CART_ABANDON"
        ])

        if not customer_purchases:
            recency_days = 999
            frequency = 0
            monetary = 0
            avg_order = 0
            dominant_cat = 0
        else:
            # Recency
            dates = []
            for p in customer_purchases:
                d = p.get("activityDate")
                if d:
                    dates.append(datetime.strptime(d[:10], "%Y-%m-%d").date())
            last_date = max(dates) if dates else date.today()
            recency_days = (date.today() - last_date).days

            # Frequency + Monetary
            frequency = len(customer_purchases)
            monetary = sum(p.get("amount", 0) or 0 for p in customer_purchases)
            avg_order = monetary / frequency if frequency > 0 else 0

            # Dominant category
            categories = [
                p.get("category") for p in all_activities
                if p.get("category")
            ]
            dominant_cat = CATEGORY_MAP.get(
                max(set(categories), key=categories.count)
                if categories else "ELECTRONICS", 0
            )

        features.append({
            "customer_id": customer_id,
            "name": f"{customer.get('name', '')} {customer.get('lastName', '')}".strip(),
            "email": customer.get("email", {}).get("primaryEmail", ""),
            "phone": customer.get("phone", {}).get("primaryPhoneNumber", ""),
            "recency_days": recency_days,
            "frequency": frequency,
            "monetary": monetary,
            "avg_order_value": avg_order,
            "dominant_category": dominant_cat,
            "browse_count": browse_count,
            "cart_abandon_count": cart_abandon_count,
            "age": customer.get("age", 0) or 0
        })

    return pd.DataFrame(features)
# ─────────────────────────────────────────
# feature_engineer.py — Build customer
# features from raw CRM data
# ─────────────────────────────────────────
import pandas as pd
from datetime import datetime, date
from collections import defaultdict
from core.config import CATEGORY_MAP

def build_customer_features(customers, purchases):
    """
    Transforms raw customer + purchase data into
    a feature matrix ready for ML models.
    Optimized to O(N+M) time complexity.
    """
    features = []

    # 🟢 THE FIX: Group all activities by customerId exactly once
    activities_by_customer = defaultdict(list)
    for p in purchases:
        cid = p.get("customerId")
        if cid:
            activities_by_customer[cid].append(p)

    for customer in customers:
        customer_id = customer.get("id")
        if not customer_id:
            continue

        # Fetch pre-grouped activities in O(1) time
        all_activities = activities_by_customer.get(customer_id, [])
        
        customer_purchases = [p for p in all_activities if p.get("activityType") == "PURCHASE"]
        
        # Standard Commerce Counters
        browse_count = sum(1 for p in all_activities if p.get("activityType") == "BROWSE")
        cart_abandon_count = sum(1 for p in all_activities if p.get("activityType") == "CART_ABANDON")
        
        # New Telemetry Counters (per Technical Spec)
        page_view_count = sum(1 for p in all_activities if p.get("activityType") == "page_view")
        form_submit_count = sum(1 for p in all_activities if p.get("activityType") == "form_submit")
        email_click_count = sum(1 for p in all_activities if p.get("activityType") == "email_click")

        if not customer_purchases:
            recency_days = 999
            frequency = 0
            monetary = 0
            avg_order = 0
            dominant_cat = 0
        else:
            # Recency
            dates = []
            for p in customer_purchases:
                d = p.get("activityDate")
                if d:
                    dates.append(datetime.strptime(d[:10], "%Y-%m-%d").date())
            last_date = max(dates) if dates else date.today()
            recency_days = (date.today() - last_date).days

            # Frequency + Monetary
            frequency = len(customer_purchases)
            monetary = sum(p.get("amount", 0) or 0 for p in customer_purchases)
            avg_order = monetary / frequency if frequency > 0 else 0

            # Dominant category (Checking all activities, not just purchases)
            categories = [p.get("category") for p in all_activities if p.get("category")]
            dominant_cat = CATEGORY_MAP.get(
                max(set(categories), key=categories.count) if categories else "ELECTRONICS", 0
            )

        features.append({
            "customer_id": customer_id,
            "name": f"{customer.get('name', '')} {customer.get('lastName', '')}".strip(),
            "email": customer.get("email", {}).get("primaryEmail", ""),
            "phone": customer.get("phone", {}).get("primaryPhoneNumber", ""),
            "recency_days": recency_days,
            "frequency": frequency,
            "monetary": monetary,
            "avg_order_value": avg_order,
            "dominant_category": dominant_cat,
            "browse_count": browse_count,
            "cart_abandon_count": cart_abandon_count,
            "page_view_count": page_view_count,       # Added Telemetry
            "form_submit_count": form_submit_count,   # Added Telemetry
            "email_click_count": email_click_count,   # Added Telemetry
            "age": customer.get("age", 0) or 0
        })

    return pd.DataFrame(features)
