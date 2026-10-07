import sys
import json
sys.path.insert(0, '/home/iddh/recommendation-engine')
from core.offer_generator import SNAPSHOT_FILE

# Load current snapshot
with open(SNAPSHOT_FILE, "r") as f:
    snapshot = json.load(f)

print("Current snapshot:")
for cid, data in snapshot.items():
    print(f"  {cid[:8]}... → {data['segment']} | RFM: {data['rfm_score']} | Recency: {data['recency_days']} | Monetary: {data['monetary']}")

# Simulate drift — move all customers up one segment
# so next engine run detects they've dropped
segment_upgrade = {
    "Dormant": {"segment": "New", "rfm_score": 2},
    "New": {"segment": "At Risk", "rfm_score": 3},
    "At Risk": {"segment": "Loyal", "rfm_score": 4},
    "Loyal": {"segment": "VIP", "rfm_score": 5},
    "VIP": {"segment": "VIP", "rfm_score": 5},
}

modified_snapshot = {}
for cid, data in snapshot.items():
    current_seg = data["segment"]
    upgrade = segment_upgrade.get(current_seg, {})
    modified_snapshot[cid] = {
        "segment": upgrade.get("segment", current_seg),
        "rfm_score": upgrade.get("rfm_score", data["rfm_score"]),
        "recency_days": max(0, data["recency_days"] - 10),  # were more recent before
        "monetary": data["monetary"] * 1.3  # were spending more before
    }

# Save modified snapshot as "yesterday"
with open(SNAPSHOT_FILE, "w") as f:
    json.dump(modified_snapshot, f, indent=4)

print("\nModified snapshot (simulating better past performance):")
for cid, data in modified_snapshot.items():
    print(f"  {cid[:8]}... → {data['segment']} | RFM: {data['rfm_score']} | Recency: {data['recency_days']} | Monetary: {data['monetary']:.0f}")

print("\n✅ Snapshot manipulated! Now run engine.py to detect drift.")
