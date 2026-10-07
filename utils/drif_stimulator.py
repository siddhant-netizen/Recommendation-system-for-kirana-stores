import json
import random
import os

SNAPSHOT_FILE = "rfm_snapshot.json"

def sabotage_snapshot(num_customers_to_sabotage=2):
    """
    Loads the daily snapshot, randomly selects customers, 
    and tanks their metrics to guarantee a 'Behavior Drift' trigger.
    """
    print("=" * 50)
    print("🧪 Behavior Drift Simulator")
    print("=" * 50)

    if not os.path.exists(SNAPSHOT_FILE):
        print(f"❌ Error: {SNAPSHOT_FILE} not found. Run your engine once to generate the baseline.")
        return

    with open(SNAPSHOT_FILE, "r") as f:
        snapshot = json.load(f)

    if not snapshot:
        print("❌ Error: Snapshot is empty.")
        return

    # Pick random customers to sabotage
    target_ids = random.sample(list(snapshot.keys()), min(num_customers_to_sabotage, len(snapshot)))
    
    print(f"🎯 Target acquired: Sabotaging {len(target_ids)} customers...\n")

    for cid in target_ids:
        original = snapshot[cid].copy()
        
        # ── The Sabotage Logic ──
        # 1. Tank the segment
        snapshot[cid]["segment"] = "Dormant"
        # 2. Drop the numerical score
        snapshot[cid]["rfm_score"] = 1
        # 3. Spike the recency (Triggering the +14 days flag)
        snapshot[cid]["recency_days"] = original.get("recency_days", 0) + 21
        # 4. Zero out the monetary spend
        snapshot[cid]["monetary"] = 0

        print(f"📉 Customer ID: {cid}")
        print(f"   Original: {original['segment']} (Recency: {original.get('recency_days', 0)}d, Spend: ${original.get('monetary', 0)})")
        print(f"   New:      {snapshot[cid]['segment']} (Recency: {snapshot[cid]['recency_days']}d, Spend: ${snapshot[cid]['monetary']})\n")

    # Save the compromised snapshot back to disk
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(snapshot, f, indent=4)

    print("✅ Sabotage complete. The snapshot has been overwritten.")
    print("🚀 Next Step: Run `python engine.py` to watch the drift detection catch these drops!")

if __name__ == "__main__":
    sabotage_snapshot()
