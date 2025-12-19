# src/telegram_notifier.py
import requests

# --- TELEGRAM CONFIGURATION ---
# Your Bot Token
TELEGRAM_BOT_TOKEN = "8300872285:AAGQzrsHJODr67DnVjdxDDIzov9aVof3o-Y"

# Your Correct Chat ID (Positive number from @userinfobot)
# Replace this if it's different, but this is the format needed.
TELEGRAM_CHAT_ID = "8333848761" 

def send_telegram_alert(message):
    """Sends a message to your Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials missing. Skipping alert.")
        return

    # Construct URL safely
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"🤖 *AI Bot Alert*\n\n{message}",
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"❌ Telegram Error: {response.text}")
        else:
            # Success!
            pass
    except Exception as e:
        print(f"❌ Telegram Connection Failed: {e}")

if __name__ == "__main__":
    # Test the alert when running this file directly
    print(f"Testing Telegram Bot...")
    send_telegram_alert("🚀 Test message from your Trading Bot!")