# raw_pincode_inspector.py
import httpx
import json

def inspect_raw_pincode_data(pincode):
    print(f"\n=================== RAW INSPECTION: {pincode} ===================")
    url = f"https://api.postalpincode.in/pincode/{pincode}"
    
    try:
        res = httpx.get(url, timeout=10.0)
        if res.status_code == 200:
            raw_json = res.json()
            
            # Print the structured text beautifully formatted
            print(json.dumps(raw_json, indent=4, ensure_ascii=False))
            
            # Print a quick breakdown summary of what the raw payload contains
            if raw_json[0]["Status"] == "Success":
                nodes = raw_json[0]["PostOffice"]
                print(f"\n📝 Raw Payload Insights for {pincode}:")
                print(f"   -> Total mapped post office dictionaries in list: {len(nodes)}")
                print(f"   -> Sample keys present in each dictionary: {list(nodes[0].keys())}")
        else:
            print(f"❌ API Error. HTTP Status: {res.status_code}")
    except Exception as e:
        print(f"⚠️ Connection Failed: {e}")

if __name__ == "__main__":
    # 1. Inspect the urban metro raw structure
    inspect_raw_pincode_data("411038") 
    
    # 2. Inspect the rural sector raw structure
    inspect_raw_pincode_data("445402")
