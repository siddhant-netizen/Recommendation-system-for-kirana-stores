# core/ai_marketer.py
import os
import json
from datetime import date
import google.generativeai as genai
from dotenv import load_dotenv

# Load variables from your local .env file
load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY", "")
if gemini_key:
    genai.configure(api_key=gemini_key)

def generate_autonomous_context_offer(weather_signal, current_temp=None):
    """
    Ingests environmental parameters and uses LLM structured reasoning to
    design a targeted retail campaign on the fly without hardcoded rules.
    """
    today = date.today()
    
    # Base seasonal metadata context fed to the model to guide its reasoning
    prompt = f"""
    You are an expert FMCG marketing strategist acting as the autonomous backend brain for a local Kirana retail store in India.
    Your task is to analyze the current hyper-local environment vectors and design a targeted promotional campaign to maximize store footfall.

    CURRENT ENV PARAMETERS:
    - Current Date: {today.isoformat()} (Use this to infer seasons like extreme summer heat, monsoons, or approaching major Indian festivals like Diwali/Eid/Holi)
    - Local Weather: {weather_signal}
    - Temperature: {f"{current_temp}°C" if current_temp else "Not Available"}

    CRITICAL REVENUE & SCHEMA RULES:
    1. applicableCategory MUST be exactly one of these uppercase strings: FOOD, CLOTHING, ELECTRONICS.
    
    2. targetSegment MUST be an exact string match selected strategically from this strict system array:
       - "VIP"           : High-value, high-frequency customers (Offer premium bundles/low discount margins).
       - "LOYAL"         : Consistent shopping segment (Offer habit-forming basket expansions).
       - "AT_RISK"       : Customers showing clear indicators of spend contraction or competitor churn.
       - "NEW"           : First-time shoppers needing an introductory hook.
       - "DORMANT"       : Inactive historical users needing deep margin rescue pricing.
       
    3. offerType MUST be exactly: DISCOUNT or CASHBACK.
    4. discountPercentage must be an integer between 5 and 30 based on the severity of the event.
    5. minimumOrderValue must be an integer multiple of 50 (e.g., 150, 200, 500) representing a logical basket spend.

    Return ONLY a raw, valid JSON object matching this exact database schema with NO extra prose or markdown wrappers:
    {{
        "name": "Catchy short campaign name referencing the situation (e.g., Summer Heatwave Chill or Monsoon Chai Fest)",
        "offerType": "DISCOUNT",
        "discountPercentage": 15,
        "minimumOrderValue": 250,
        "applicableCategory": "FOOD",
        "targetSegment": "ALL_CUSTOMERS"
    }}
    """

    try:
        # Utilizing the lightning-fast, developer-free-tier flash model
        model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Enforce strict JSON output mode via the API configurations
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Parse the structured JSON response
        offer_template = json.loads(response.text.strip())
        return offer_template

    except Exception as e:
        print(f"    ⚠️ Autonomous AI Layer Exception: {e}")
        return None
