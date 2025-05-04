# playwright_login.py

from playwright.sync_api import sync_playwright
import json
from dotenv import load_dotenv
import os

load_dotenv("config.env")  # 明确指定路径

ZLIB_EMAIL = os.getenv("ZLIB_EMAIL")
ZLIB_PASSWORD = os.getenv("ZLIB_PASSWORD")

def fetch_zlib_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://z-lib.fm/login")

        page.fill('input[name="email"]', ZLIB_EMAIL)
        page.fill('input[name="password"]', ZLIB_PASSWORD)
        page.click('button[type="submit"]')

        page.wait_for_timeout(5000)

        cookies = page.context.cookies()
        with open("zlib_cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)

        print(f"✅ Saved {len(cookies)} cookies to zlib_cookies.json")
        browser.close()

if __name__ == "__main__":
    fetch_zlib_cookies()

