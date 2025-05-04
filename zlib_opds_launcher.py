# zlib_opds_launcher.py

import subprocess, os, sys, time
from dotenv import load_dotenv

load_dotenv("config.env")  # 明确指定路径

ZLIB_EMAIL = os.getenv("ZLIB_EMAIL")
ZLIB_PASSWORD = os.getenv("ZLIB_PASSWORD")

def check_env():
    if not ZLIB_EMAIL or not ZLIB_PASSWORD:
        print("❌ Please set ZLIB_EMAIL and ZLIB_PASSWORD in .env")
        sys.exit(1)

def playwright_login():
    print("🔐 Logging in to Z-Lib via Playwright...")
    subprocess.run([sys.executable, "playwright_login.py"], check=True)

def launch_fastapi():
    print("🚀 Starting FastAPI at http://localhost:8000/opds")
    subprocess.run(["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    check_env()
    playwright_login()
    launch_fastapi()

