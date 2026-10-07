# ─────────────────────────────────────────
# data_fetcher.py — All Twenty API calls
# Refactored: Max Pagination & Session Lock
# ─────────────────────────────────────────
import requests
import time
import urllib.parse
from core.config import API_KEY, BASE_URL

# 1. ENFORCE THE SESSION 
# Keeps the TCP connection alive to prevent Docker network drops
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
})

def _make_request(method, url, payload=None, retries=3):
    """
    Centralized HTTP request handler with rate limit protection.
    """
    for attempt in range(retries):
        if method.upper() == 'GET':
            response = session.get(url)
        elif method.upper() == 'POST':
            response = session.post(url, json=payload)
        elif method.upper() == 'PATCH':
            response = session.patch(url, json=payload)
        elif method.upper() == 'DELETE':
            response = session.delete(url)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        if response.status_code == 429:
            wait_time = int(response.headers.get("Retry-After", 61))
            print(f"  ⚠️ Rate limited, waiting {wait_time}s...")
            time.sleep(wait_time)
            continue
            
        # Micro-delay to strictly pace requests under the 90/min limit
        time.sleep(0.5) 
        return response
    return None

# 2. MAX OUT THE PAGE SIZE
# Pulls data in massive chunks to minimize total GET requests
def get_all(endpoint, page_size=1000):
    """
    Fetches all records with pagination support safely.
    """
    all_records = []
    cursor = None

    while True:
        url = f"{BASE_URL}/rest/{endpoint}?depth=1&limit={page_size}"
        if cursor:
            safe_cursor = urllib.parse.quote(cursor)
            url += f"&cursor={safe_cursor}"

        response = _make_request('GET', url)
        
        if not response or not response.ok:
            error_code = response.status_code if response else 'Timeout'
            raise Exception(f"❌ Fatal Error fetching {endpoint}: HTTP {error_code}. Response: {response.text if response else 'None'}")

        data = response.json()
        raw_data = data.get("data", [])

        if isinstance(raw_data, list):
            records = raw_data
        elif isinstance(raw_data, dict):
            values = list(raw_data.values())
            records = values[0] if values else []
        else:
            records = []

        all_records.extend(records)

        page_info = data.get("pageInfo", {})
        has_next = page_info.get("hasNextPage", False)
        cursor = page_info.get("endCursor", None)

        if not has_next or not cursor:
            break

    return all_records

# --- Specific Fetchers ---
def get_customers():
    return get_all("customers")

def get_purchases():
    return get_all("purchases")

def get_offers():
    return get_all("offers")

def get_customer_offers():
    return get_all("customeroffers")

def get_customer_groups():
    return get_all("customerGroups")

# --- CRUD Operations ---
def create_record(endpoint, payload):
    return _make_request('POST', f"{BASE_URL}/rest/{endpoint}", payload=payload)

def update_record(endpoint, record_id, payload):
    return _make_request('PATCH', f"{BASE_URL}/rest/{endpoint}/{record_id}", payload=payload)

def delete_record(endpoint, record_id):
    return _make_request('DELETE', f"{BASE_URL}/rest/{endpoint}/{record_id}")
