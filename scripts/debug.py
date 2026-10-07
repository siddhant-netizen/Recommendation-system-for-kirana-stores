import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TWENTY_API_KEY", "")
BASE_URL = os.getenv("TWENTY_BASE_URL", "http://localhost:3000")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

objects = ["customers", "purchases", "offers", "customerGroups", "customeroffers"]

for obj in objects:
    resp = requests.get(f"{BASE_URL}/rest/{obj}?depth=1&limit=1", headers=HEADERS)
    data = resp.json()
    values = list(data.get("data", {}).values())
    if values and values[0]:
        record = values[0][0]
        print(f"\n=== {obj.upper()} ===")
        for key in record.keys():
            print(f"  {key}")
    else:
        print(f"\n=== {obj.upper()} === (no records found)")
