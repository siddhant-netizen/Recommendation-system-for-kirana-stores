import sys
sys.path.insert(0, '/home/iddh/recommendation-engine')
from core.locality_scorer import adjust_offers_for_locality

BASE_OFFERS = {
    "20% Off Electronics":      0.50,
    "10% Cashback on Clothing": 0.45,
    "Free Shipping on Food":    0.40,
    "Win Back Deal":            0.35,
    "Re-engage Bundle":         0.30,
    "30% Off All Categories":   0.25
}

locations = [
    "Tawang Arunachal Pradesh",
    "Kothrud Pune Maharashtra"
]

for location in locations:
    print(f"\n{'='*60}")
    print(f"  📍 Store Location: {location}")
    print(f"{'='*60}")

    results, profile = adjust_offers_for_locality(BASE_OFFERS, location)

    print(f"\n  🎯 Ranked Offers:")
    print(f"  {'Offer':<30} {'Base':>6} {'Boost':>6} {'Final':>6}")
    print("  " + "-"*55)
    for offer, base, boost, final in results:
        print(f"  {offer:<30} {base:>6.2f} {boost:>6.2f} {final:>6.2f}")

    print(f"\n  ✅ Top recommendation: {results[0][0]}")
