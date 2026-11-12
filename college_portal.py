"""
college_portal.py — UPES Student Portal Automation & Class Schedule Tracking.

Provides automated login, timetable queries, and secure credential storage for
Nakul's UPES student portal (myupes-beta.upes.ac.in).
"""

import time
import webbrowser
import pyperclip
import config
import memory_manager

PORTAL_URL = "https://myupes-beta.upes.ac.in/oneportal/app/auth/login"

def save_credentials(username: str, password: str) -> str:
    """
    Saves UPES portal student ID and password securely in Windows Credential Manager.
    """
    u = username.strip()
    p = password.strip()
    config.set_value("upes_portal_username", u)
    config.set_value("upes_portal_password", p)
    memory_manager.remember_fact(f"UPES student portal ID is {u}")
    return f"Saved UPES portal credentials for student ID {u}."

def get_credentials() -> tuple[str, str]:
    """Retrieves saved UPES credentials."""
    return config.get("upes_portal_username") or "", config.get("upes_portal_password") or ""

def open_portal() -> str:
    """Opens the official UPES portal in the default web browser."""
    webbrowser.open(PORTAL_URL)
    return "Opened the UPES student portal."

def login_and_open() -> str:
    """
    Opens the UPES student portal and prepares login credentials.
    """
    u, p = get_credentials()
    if not u or not p:
        open_portal()
        return "I opened the UPES portal. You haven't saved your login credentials yet. Just tell me: 'save my UPES credentials' to set them up."

    # Copy student ID to clipboard so the user can paste instantly
    pyperclip.copy(u)
    webbrowser.open(PORTAL_URL)
    return f"Opening UPES portal. Your student ID {u} is copied to your clipboard."

def check_timetable() -> str:
    """
    Checks today's timetable on the UPES portal.
    """
    u, p = get_credentials()
    if not u or not p:
        return "I need your UPES credentials to check your classes. Tell me your UPES username and password to set it up."

    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        driver.get(PORTAL_URL)
        time.sleep(3)
        inputs = driver.find_elements(By.TAG_NAME, "input")
        if len(inputs) >= 2:
            inputs[0].send_keys(u)
            inputs[1].send_keys(p)
            buttons = driver.find_elements(By.TAG_NAME, "button")
            if buttons:
                buttons[0].click()
                time.sleep(4)
                return "Logged into UPES portal. Please check your schedule dashboard."
        driver.quit()
        return "Attempted login to UPES portal."
    except Exception as e:
        open_portal()
        return f"Opened UPES portal in your browser: {e}"
