# export_twenty_schema.py
import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()

# Replace with your hosted instance URI or local container port
TWENTY_CRM_BASE_URL = os.getenv("TWENTY_BASE_URL", "http://localhost:3000") + "/api/v1"
API_KEY = os.getenv("TWENTY_API_KEY", "")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def download_crm_metadata_schema():
    print("📡 Extracting active data model blueprints via Metadata API...")
    
    # Hits the metadata sub-path designed to extract the layout schema structural rules
    url = f"{TWENTY_CRM_BASE_URL}/metadata/objects"
    
    try:
        response = httpx.get(url, headers=headers, timeout=15.0)
        if response.status_code == 200:
            schema_data = response.json()
            
            # Save the schema structure to a local JSON document
            output_file = "twenty_crm_schema.json"
            with open(output_file, "w") as f:
                json.dump(schema_data, f, indent=4)
                
            print(f"✅ Schema exported successfully! Sent definitions to: {output_file}")
            
            # Quick summary look at the objects available to the team
            objects = schema_data.get("data", [])
            print(f"📦 Active Entities Isolated: {[obj.get('nameSingular') for obj in objects]}")
            
        else:
            print(f"❌ Failed to read Metadata Schema. Status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Metadata extraction failed: {e}")

if __name__ == "__main__":
    download_crm_metadata_schema()
