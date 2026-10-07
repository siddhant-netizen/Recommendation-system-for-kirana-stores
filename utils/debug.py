import sys
sys.path.insert(0, '/home/iddh/recommendation-engine')
from core.data_fetcher import session, BASE_URL
import json

resp = session.get(f"{BASE_URL}/rest/offers?depth=1&limit=1")
data = resp.json()
values = list(data.get("data", {}).values())
if values and values[0]:
    customer = values[0][0]
    print("offer fields:")
    for key in customer.keys():
        print(f"  {key}")
