import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TWENTY_API_KEY", "")
BASE_URL = os.getenv("TWENTY_BASE_URL", "http://localhost:3000")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

resp = requests.get(f"{BASE_URL}/rest/open-api/core", headers=HEADERS)
data = resp.json()
schemas = data.get("components", {}).get("schemas", {})

for name, schema in schemas.items():
    if "customergroup" in name.lower() and "offer" not in name.lower():
        print(f"\n--- {name} ---")
        props = schema.get("properties", {})
        for field, details in props.items():
            print(f"  {field}: {details.get('type', '')} {details.get('enum', '')}")
