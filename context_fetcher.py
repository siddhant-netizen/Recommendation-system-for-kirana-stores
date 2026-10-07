import requests
from datetime import date

def get_store_weather(lat, lon):
    """
    Queries Open-Meteo for hyper-local weather.
    Converts WMO codes into simple internal actions.
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "timezone": "Asia/Kolkata"
        }
        resp = requests.get(url, params=params, timeout=5)
        if resp.ok:
            weather_code = resp.json().get("current_weather", {}).get("weathercode", 0)
            # WMO Codes: 51-67 are rain, 80-82 are rain showers
            if weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
                return "RAIN"
            elif weather_code in [71, 73, 75, 77, 85, 86]:
                return "COLD_SNAP"
        return "NORMAL"
    except Exception as e:
        print(f"  ⚠️ Context Warning: Weather query skipped ({e})")
        return "NORMAL"

def get_store_cultural_context(api_key, country_code="IN", state_code=None):
    """
    Queries Calendarific for regional or national holidays happening TODAY.
    """
    if not api_key or api_key == "YOUR_MOCK_KEY_HERE":
        return "NONE"
        
    try:
        current_date = date.today()
        url = "https://calendarific.com/api/v2/holidays"
        params = {
            "api_key": api_key,
            "country": country_code,
            "year": current_date.year,
            "month": current_date.month,
            "day": current_date.day
        }
        if state_code:
            params["location"] = state_code

        resp = requests.get(url, params=params, timeout=5)
        if resp.ok:
            holidays = resp.json().get("response", {}).get("holidays", [])
            for holiday in holidays:
                h_type = [t.lower() for t in holiday.get("type", [])]
                if "national holiday" in h_type or "religious holiday" in h_type or "observance" in h_type:
                    return holiday.get("name", "").upper().replace(" ", "_")
        return "NONE"
    except Exception as e:
        print(f"  ⚠️ Context Warning: Calendarific sync skipped ({e})")
        return "NONE"
