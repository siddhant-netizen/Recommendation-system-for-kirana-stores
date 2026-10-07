import json
import random
import os

SNAPSHOT_FILE = "rfm_snapshot.json"

def inflate_snapshot_for_extreme_drift(num_customers_to_sabotage=3):
    """
    Loads the daily snapshot and artificially inflates historical metrics.
    By making 'yesterday' look like a perfect VIP state, the real data 
    fetched 'today' will register as a catastrophic behavioral drop.
    """
    print("=" * 50)
    print("🧪 Extreme Behavior Drift Simulator")
    print("=" * 50)

    if not os.path.exists(SNAPSHOT_FILE):
        print(f"❌ Error: {SNAPSHOT_FILE} not found. Run your engine once to generate the baseline.")
        return

    with open(SNAPSHOT_FILE, "r") as f:
        snapshot = json.load(f)

    if not snapshot:
        print("❌ Error: Snapshot is empty.")
        return

    # Pick random customers to target
    target_ids = random.sample(list(snapshot.keys()), min(num_customers_to_sabotage, len(snapshot)))
    
    print(f"🎯 Target acquired: Setting up {len(target_ids)} customers for a massive fall...\n")

    for cid in target_ids:
        original = snapshot[cid].copy()
        
        # ── The Extreme Setup Logic ──
        # We make their past look absolutely perfect so their present looks awful.
        snapshot[cid]["segment"] = "VIP"
        snapshot[cid]["rfm_score"] = 5
        snapshot[cid]["recency_days"] = 0        # They bought "yesterday"
        snapshot[cid]["monetary"] = 50000        # They spent $50,000

        print(f"📈 Customer ID: {cid}")
        print(f"   Original Past: {original['segment']} (Recency: {original.get('recency_days', 0)}d, Spend: ${original.get('monetary', 0)})")
        print(f"   Forged Past:   {snapshot[cid]['segment']} (Recency: {snapshot[cid]['recency_days']}d, Spend: ${snapshot[cid]['monetary']})\n")

    # Save the compromised snapshot back to disk
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump(snapshot, f, indent=4)

    print("✅ Sabotage complete. The historical snapshot has been maxed out.")
    print("🚀 Next Step: Run `python engine.py`.")
    print("   The engine will compare their real CRM data against this forged VIP past,")
    print("   triggering a massive 8+ point downward drift score!")

if __name__ == "__main__":
    inflate_snapshot_for_extreme_drift()
