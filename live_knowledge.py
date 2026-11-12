"""
live_knowledge.py — Real-Time Web, Weather, News & GitHub Knowledge Engine for Jarvis 2.0.

Provides direct access to live internet information without requiring the user
to browse manually or read messy websites. Operates with zero API keys.
"""

import requests
import urllib.parse
import re
import xml.etree.ElementTree as ET

def _clean_speech_text(text: str) -> str:
    """Strips unprintable unicode/emojis so console and TTS engine pronounce words cleanly."""
    if not text:
        return ""
    # Strip emojis and non-latin1 characters that break Windows console
    return text.encode('ascii', 'ignore').decode('ascii').strip()
WMO_WEATHER_CODES = {
    0: "clear skies",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "foggy",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "slight snow fall",
    73: "moderate snow fall",
    75: "heavy snow fall",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    95: "thunderstorm with slight hail",
    96: "thunderstorm with moderate hail"
}

def get_live_weather(location: str = "Dehradun") -> str:
    """
    Fetches real-time weather conditions, temperature, humidity, and forecast
    for any specified city (defaults to Dehradun for UPES campus).
    """
    loc_clean = location.strip() or "Dehradun"
    try:
        # Step 1: Geocoding
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(loc_clean)}&count=1&language=en&format=json"
        geo_resp = requests.get(geo_url, timeout=4).json()
        if not geo_resp.get("results"):
            return f"I could not locate '{loc_clean}' on the weather satellite."
        
        place = geo_resp["results"][0]
        lat, lon = place["latitude"], place["longitude"]
        city_name = place.get("name", loc_clean)
        country = place.get("country", "")

        # Step 2: Forecast data
        f_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m"
            f"&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
        )
        f_resp = requests.get(f_url, timeout=4).json()
        cur = f_resp.get("current", {})
        daily = f_resp.get("daily", {})

        temp = cur.get("temperature_2m")
        feels_like = cur.get("apparent_temperature", temp)
        humidity = cur.get("relative_humidity_2m", 0)
        wind = cur.get("wind_speed_10m", 0)
        w_code = cur.get("weather_code", 0)
        desc = WMO_WEATHER_CODES.get(w_code, "fair weather")

        max_t = daily.get("temperature_2m_max", [temp])[0]
        min_t = daily.get("temperature_2m_min", [temp])[0]

        return (
            f"In {city_name}, it is currently {temp:.1f}°C with {desc}. "
            f"Feels like {feels_like:.1f}°C with {humidity}% humidity. "
            f"Today's high is expected to reach {max_t:.1f}°C with a low of {min_t:.1f}°C."
        )
    except Exception as e:
        return f"Unable to retrieve live weather right now: {e}"

def get_live_news(topic: str = "") -> str:
    """
    Fetches real-time breaking news or specific topic headlines from Google News RSS.
    """
    try:
        if topic.strip():
            encoded = urllib.parse.quote(topic.strip())
            rss_url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
        else:
            rss_url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"

        resp = requests.get(rss_url, headers={"User-Agent": "JarvisAI/2.0"}, timeout=5)
        root = ET.fromstring(resp.content)
        items = root.findall(".//item")
        if not items:
            return "No news items found for that query right now."

        headlines = []
        for it in items[:4]:
            title = it.find("title").text if it.find("title") is not None else ""
            # Strip source suffix if present (e.g. " - The Hindu")
            if " - " in title:
                title = title.rsplit(" - ", 1)[0]
            if title and title not in headlines:
                headlines.append(title)

        if not headlines:
            return "Unable to parse current headlines."

        intro = f"Here are the top headlines{' on ' + topic if topic else ''}: "
        return intro + " ... ".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
    except Exception as e:
        return f"Unable to fetch live news at the moment: {e}"

def search_live_knowledge(query: str) -> str:
    """
    Directly queries Wikipedia and DuckDuckGo to extract instant factual answers
    for technical, historical, scientific, or general knowledge questions.
    """
    q_clean = query.strip()
    if not q_clean:
        return "Please ask a specific knowledge question."

    # Try Wikipedia REST summary first
    try:
        formatted = urllib.parse.quote(q_clean.replace(" ", "_"))
        wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{formatted}"
        w_resp = requests.get(wiki_url, headers={"User-Agent": "JarvisAI/2.0"}, timeout=4)
        if w_resp.status_code == 200:
            data = w_resp.json()
            extract = data.get("extract", "")
            title = data.get("title", "")
            if extract and len(extract) > 40:
                # Return first 2-3 sentences
                sentences = re.split(r'(?<=[.!?]) +', extract)
                short_summary = " ".join(sentences[:3])
                return f"{title}: {short_summary}"
    except Exception:
        pass

    # Fallback to DuckDuckGo Instant Answer
    try:
        ddg_url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(q_clean)}&format=json&no_html=1&skip_disambig=1"
        d_resp = requests.get(ddg_url, headers={"User-Agent": "JarvisAI/2.0"}, timeout=4).json()
        abstract = d_resp.get("AbstractText", "")
        heading = d_resp.get("Heading", "")
        if abstract:
            return f"{heading}: {abstract}"
    except Exception:
        pass

    return f"I could not extract an instant fact sheet for '{query}'. Would you like me to open the web search results in your browser?"

def get_github_overview(repo_or_user: str) -> str:
    """
    Retrieves public repository metrics, star counts, primary languages, and descriptions from GitHub.
    """
    clean_q = repo_or_user.strip()
    if not clean_q:
        clean_q = "machine learning"
    try:
        if "/" in clean_q:
            # Specific repo
            url = f"https://api.github.com/repos/{clean_q}"
            r = requests.get(url, headers={"User-Agent": "JarvisAI/2.0"}, timeout=4)
            if r.status_code == 200:
                data = r.json()
                name = data.get("full_name")
                stars = data.get("stargazers_count", 0)
                lang = data.get("language", "Various")
                desc = _clean_speech_text(data.get("description", "No description provided."))
                return f"GitHub Repository {name}: {stars:,} stars, written in {lang}. Description: {desc}"
        
        # Search repositories
        s_url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(clean_q)}&sort=stars&order=desc"
        s_resp = requests.get(s_url, headers={"User-Agent": "JarvisAI/2.0"}, timeout=4)
        if s_resp.status_code == 200:
            items = s_resp.json().get("items", [])
            if items:
                top = items[0]
                desc = _clean_speech_text(top.get('description', ''))
                return f"Top GitHub repository for '{clean_q}' is {top['full_name']} with {top['stargazers_count']:,} stars in {top.get('language', 'General')}. Description: {desc}"

        return f"No matching public GitHub repository found for '{clean_q}'."
    except Exception as e:
        return f"Unable to reach GitHub API: {e}"

if __name__ == "__main__":
    print("Testing live weather in Dehradun:")
    print(get_live_weather("Dehradun"))
    print("\nTesting live news:")
    print(get_live_news("AI"))
    print("\nTesting instant knowledge:")
    print(search_live_knowledge("Neural network"))
    print("\nTesting GitHub search:")
    print(get_github_overview("PyTorch"))
