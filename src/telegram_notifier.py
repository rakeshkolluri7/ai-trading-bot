# src/telegram_notifier.py
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- TELEGRAM CONFIGURATION ---
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_alert(message):
    """Sends a message to your Telegram bot."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Telegram Error [{response.status_code}]: {response.text}")
        else:
            print(f"✅ Telegram Sent: {message.splitlines()[0]}...")
    except Exception as e:
        print(f"❌ Telegram Connection Failed: {e}")

if __name__ == "__main__":
    # Test the alert when running this file directly
    print(f"Testing Telegram Bot...")
    send_telegram_alert("🚀 Test message from your Secure Trading Bot!")