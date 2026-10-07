import pandas as pd
from core.config import CATEGORY_REVERSE, SEGMENT_API_MAP
from core.data_fetcher import (
    get_customer_groups,
    create_record,
    update_record
)

def sync_customer_groups(df):
    """
    Calculates aggregate stats per segment and
    upserts them into the CustomerGroups object in Twenty.
    Returns a mapping of segment_name -> group_id.
    """
    if df.empty:
        print("⚠️ No data to sync groups")
        return {}

    print("\nSyncing Customer Groups...")

    # Calculate group analytics
    stats = df.groupby("segment").agg(
        size=("customer_id", "count"),
        avg_spend=("monetary", "mean"),
        avg_frequency=("frequency", "mean"),
        dominant_category=("dominant_category", lambda x: x.mode()[0] if not x.empty else 0)
    ).reset_index()

    # Fetch existing groups to avoid duplicates
    existing_groups = get_customer_groups()
    group_map = {
        g.get("name"): g.get("id")
        for g in existing_groups
        if g.get("name")
    }

    group_id_mapping = {}

    for _, row in stats.iterrows():
        seg_name = row["segment"]
        
        # 1. FIXED: Ensure Enum values are UPPER_SNAKE_CASE (e.g. HOME_APPLIANCES)
        raw_cat = CATEGORY_REVERSE.get(int(row["dominant_category"]), "ELECTRONICS")
        dom_cat = raw_cat.upper().replace(" ", "_")

        payload = {
            "name": seg_name,
            "groupName": seg_name,
            "rfmSegment": SEGMENT_API_MAP.get(seg_name, "NEW"),
            "size": int(row["size"]),
            "avgspend": round(float(row["avg_spend"]), 2),
            "avgpurchasefrequency": round(float(row["avg_frequency"]), 2),
            "dominantCategory": dom_cat
        }

        # 2. FIXED: Changed object name to all-lowercase "customergroups"
        if seg_name in group_map:
            # Update existing group
            g_id = group_map[seg_name]

            resp = update_record("customerGroups", g_id, payload)
            if resp and resp.ok:
                group_id_mapping[seg_name] = g_id
                print(f"    DEBUG group_id_mapping: {seg_name} → {g_id}")
                print(f"  ✅ Updated group: {seg_name} ({int(row['size'])} customers)")
            else:
                # 3. FIXED: Added resp.text so we can see the exact Twenty API validation error
                print("failing to update old")
                error_msg = resp.text if resp else "No response"
                print(f"  ❌ Failed to update {seg_name}: {resp.status_code if resp else 'N/A'} - {error_msg}")
        else:
            # Create new group
            resp = create_record("customerGroups", payload)
            if resp and resp.ok:
                resp_data = resp.json().get("data", {})
                new_id = (
                    resp_data.get("id") or
                    resp_data.get("createCustomerGroup", {}).get("id")
                )
                group_id_mapping[seg_name] = new_id
                print(f"  ✅ Created group: {seg_name} ({int(row['size'])} customers)")
            else:
                print("failing to create new")
                error_msg = resp.text if resp else "No response"
                print(f"  ❌ Failed to create {seg_name}: {resp.status_code if resp else 'N/A'} - {error_msg}")

    print(f"✅ Synced {len(group_id_mapping)} customer groups\n")
    return group_id_mapping

def link_customer_to_group(customer_id, group_id):
    if not group_id:
        print(f"  ⚠️ No group_id provided for customer {customer_id}")
        return
    resp = update_record("customers", customer_id, {"customerGroupsId": group_id} )
    if not resp.ok:
        print(f"  ⚠️ Failed to link {customer_id} → {resp.status_code} → {resp.json()}")
    else:
        print(f"  ✅ Linked customer {customer_id} to group {group_id}")
