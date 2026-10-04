import os
import re
import requests
from dotenv import load_dotenv
from TextToSpeech.Fast_DF_TTS import speak

load_dotenv()

DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Mangalore")

WEATHER_PATTERNS = [
    r'\b(weather)\b',
    r'\b(temperature)\b',
    r'\b(forecast)\b',
    r'\b(how(\'?s| is| will)\s+the\s+weather)\b',
    r'\b(how(\'?s| is)\s+the\s+weather\s+today)\b',
    r'\b(will\s+it\s+rain)\b',
    r'\b(is\s+it\s+going\s+to\s+rain)\b',
    r'\b(chance\s+of\s+rain)\b',
    r'\b(is\s+it\s+raining)\b',
    r'\b(umbrella)\b',
    r'\b(need\s+an\s+umbrella)\b',
    r'\b(check\s+weather)\b'
]

def safe_print(msg: str):
    """Safely print text to Windows console without encoding exceptions."""
    try:
        print(msg)
    except Exception:
        try:
            print(str(msg).encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass

def is_weather_query(text: str) -> bool:
    """Check if the given text is a weather inquiry."""
    lower = text.lower().strip()
    for pattern in WEATHER_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False

def extract_city(text: str, default: str = DEFAULT_CITY) -> str:
    """Extract city/location from user query, or return default city."""
    patterns = [
        r'(?:weather|temperature|forecast|rain|umbrella)\s+(?:in|for|at|of)\s+([a-zA-Z\s]+?)(?:\s+today|\s+tomorrow|\s+now|\?|$)',
        r'\bin\s+([a-zA-Z\s]+?)(?:\s+today|\s+tomorrow|\s+now|\?|$)'
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            city = m.group(1).strip()
            city = re.sub(r'\b(today|tomorrow|now|please|right now|the|day after tomorrow)\b', '', city, flags=re.IGNORECASE).strip()
            if city and len(city) > 1:
                return city.title()
    return default

def fetch_weather_wttr(city: str) -> dict:
    """Fetch live weather from wttr.in."""
    url = f"https://wttr.in/{city.replace(' ', '+')}?format=j1"
    res = requests.get(url, timeout=7)
    if res.status_code == 200:
        data = res.json()
        curr = data['current_condition'][0]
        temp = curr.get('temp_C')
        condition = curr.get('weatherDesc', [{}])[0].get('value', '').strip()
        humidity = curr.get('humidity')
        wind = curr.get('windspeedKmph')
        
        # Max rain chance across today's hourly forecasts
        weather_today = data.get('weather', [{}])[0]
        hourly = weather_today.get('hourly', [])
        rain_chances = [int(h.get('chanceofrain', 0)) for h in hourly if 'chanceofrain' in h]
        rain_chance = max(rain_chances) if rain_chances else 0

        return {
            "city": city,
            "temp": temp,
            "condition": condition,
            "rain_chance": rain_chance,
            "humidity": humidity,
            "wind": wind,
            "is_tomorrow": False,
            "success": True
        }
    return {"city": city, "success": False}

def fetch_tomorrow_forecast(city: str) -> dict:
    """Fetch tomorrow's forecast and rain probability using Open-Meteo."""
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city.replace(' ', '+')}&count=10"
        geo_res = requests.get(geo_url, timeout=7).json()
        results = geo_res.get('results', [])
        if not results:
            return {"city": city, "success": False}
            
        best = None
        for r in results:
            if r.get("country", "").lower() == "india":
                best = r
                break
        if not best:
            best = max(results, key=lambda x: x.get("population", 0) or 0)
            
        lat = best['latitude']
        lon = best['longitude']
        
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"
            f"&timezone=auto"
        )
        data = requests.get(url, timeout=7).json()
        daily = data.get("daily", {})
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        rain_probs = daily.get("precipitation_probability_max", [])
        codes = daily.get("weather_code", [])
        
        wmo_codes = {
            0: "clear skies", 1: "mainly clear skies", 2: "partly cloudy skies", 3: "overcast skies",
            45: "foggy weather", 51: "light drizzle", 61: "slight rain", 63: "moderate rain",
            65: "heavy rain", 80: "rain showers", 95: "thunderstorms"
        }
        code = codes[1] if len(codes) > 1 else 0
        condition = wmo_codes.get(code, "partly cloudy skies")
        min_temp = int(round(min_temps[1])) if len(min_temps) > 1 else "N/A"
        max_temp = int(round(max_temps[1])) if len(max_temps) > 1 else "N/A"
        rain_chance = int(rain_probs[1]) if len(rain_probs) > 1 else 0
        
        return {
            "city": city,
            "min_temp": min_temp,
            "max_temp": max_temp,
            "condition": condition,
            "rain_chance": rain_chance,
            "is_tomorrow": True,
            "success": True
        }
    except Exception:
        return {"city": city, "success": False}

def fetch_weather_open_meteo(city: str) -> dict:
    """Fallback weather fetcher for today using Open-Meteo API."""
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city.replace(' ', '+')}&count=10"
        geo_res = requests.get(geo_url, timeout=7).json()
        results = geo_res.get('results', [])
        if not results:
            return {"city": city, "success": False}
            
        best = None
        for r in results:
            if r.get("country", "").lower() == "india":
                best = r
                break
        if not best:
            best = max(results, key=lambda x: x.get("population", 0) or 0)

        lat = best['latitude']
        lon = best['longitude']
        
        meteo_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
            f"&hourly=precipitation_probability"
        )
        m_res = requests.get(meteo_url, timeout=7).json()
        curr = m_res.get('current', {})
        temp = curr.get('temperature_2m')
        humidity = curr.get('relative_humidity_2m')
        wind = curr.get('wind_speed_10m')
        
        wmo_codes = {
            0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
            45: "Foggy", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
            55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
            80: "Rain showers", 95: "Thunderstorm"
        }
        code = curr.get('weather_code', 0)
        condition = wmo_codes.get(code, "Clear")
        hourly_rain = m_res.get('hourly', {}).get('precipitation_probability', [])
        rain_chance = max(hourly_rain[:24]) if hourly_rain else 0

        return {
            "city": city,
            "temp": int(round(temp)) if temp is not None else "N/A",
            "condition": condition,
            "rain_chance": rain_chance,
            "humidity": humidity,
            "wind": int(round(wind)) if wind is not None else "N/A",
            "is_tomorrow": False,
            "success": True
        }
    except Exception:
        return {"city": city, "success": False}

def get_live_weather(city: str, is_tomorrow: bool = False) -> dict:
    """Fetch live weather data from available providers with resilient fallback."""
    if is_tomorrow:
        data = fetch_tomorrow_forecast(city)
        if data.get("success"):
            return data
            
    # Try wttr.in first for today
    try:
        data = fetch_weather_wttr(city)
        if data.get("success"):
            return data
    except Exception:
        pass

    # Try Open-Meteo fallback
    try:
        data = fetch_weather_open_meteo(city)
        if data.get("success"):
            return data
    except Exception:
        pass

    return {"city": city, "success": False}

def format_weather_response(query_text: str, data: dict) -> str:
    """Format weather details into natural speech."""
    if not data.get("success"):
        return "Sorry, I couldn't retrieve the weather right now."

    city = data["city"]
    lower_query = query_text.lower()
    is_tomorrow = data.get("is_tomorrow", False)
    is_umbrella_query = "umbrella" in lower_query
    is_rain_query = "rain" in lower_query or is_umbrella_query

    # Tomorrow's response
    if is_tomorrow:
        min_temp = data["min_temp"]
        max_temp = data["max_temp"]
        condition = data["condition"]
        rain = data["rain_chance"]
        
        if is_umbrella_query:
            if rain > 40:
                return f"Yes, you should definitely take an umbrella tomorrow in {city}, as there is a {rain} percent chance of rain."
            else:
                return f"You probably won't need an umbrella tomorrow in {city}, as the chance of rain is only {rain} percent."
                
        if is_rain_query:
            if rain > 40:
                return f"Yes, rain is expected tomorrow in {city} with a {rain} percent chance of precipitation and temperatures between {min_temp} and {max_temp} degrees Celsius."
            else:
                return f"Rain is unlikely tomorrow in {city} with only a {rain} percent chance of precipitation and {condition}."
                
        return f"Tomorrow in {city}, expect {condition} with temperatures between {min_temp} and {max_temp} degrees Celsius and a {rain} percent chance of rain."

    # Today's response
    temp = data["temp"]
    condition = data["condition"]
    rain = data["rain_chance"]
    humidity = data.get("humidity")
    wind = data.get("wind")

    if is_umbrella_query:
        if rain > 40:
            return f"Yes, you should take an umbrella today in {city}. There is a {rain} percent chance of rain with {condition.lower()} skies."
        else:
            return f"You likely won't need an umbrella today in {city}, with only a {rain} percent chance of rain."

    if is_rain_query:
        if rain > 40:
            msg = f"Yes, there is a {rain} percent chance of rain today in {city} with {condition.lower()} conditions and temperature around {temp} degrees Celsius."
        else:
            msg = f"Today in {city}, rain is unlikely with only a {rain} percent chance of rain and {condition.lower()} skies at {temp} degrees Celsius."
    else:
        msg = f"Today in {city}, the temperature is around {temp} degrees Celsius with {condition.lower()} conditions and a {rain} percent chance of rain."
        if humidity:
            msg += f" The humidity is {humidity} percent"
        if wind:
            msg += f" with winds around {wind} kilometers per hour."

    return msg

def get_weather_response(text: str) -> str:
    """Fetch weather data and return formatted response text without speaking."""
    city = extract_city(text)
    is_tomorrow = "tomorrow" in text.lower()
    data = get_live_weather(city, is_tomorrow=is_tomorrow)
    return format_weather_response(text, data)

def handle_weather_command(text: str) -> str:
    """Fetch weather for detected city, speak via TTS, log, and return response."""
    response = get_weather_response(text)
    
    safe_print(f"\n[Jarvis - Weather]: {response}")
    try:
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"\nYou : {text}\njarvis : {response}\n")
    except Exception:
        pass
        
    speak(response)
    return response

if __name__ == "__main__":
    print(handle_weather_command("Jarvis, will it rain tomorrow?"))
