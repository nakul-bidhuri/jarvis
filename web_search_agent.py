"""
web_search_agent.py — Live Web Queries & Online Search for Jarvis.

Handles Google searches, current events, tech lookups, and career data queries.
"""

import webbrowser
import urllib.parse

def search_google(query: str, open_browser: bool = True) -> str:
    """
    Searches Google for the specified query and opens the results in the browser.
    """
    clean_q = query.strip()
    encoded = urllib.parse.quote(clean_q)
    url = f"https://www.google.com/search?q={encoded}"
    if open_browser:
        webbrowser.open(url)
        return f"Searching Google for '{clean_q}' in your browser."
    return f"Search URL: {url}"

def open_website(url: str) -> str:
    """Opens a website URL in the default web browser."""
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}."
