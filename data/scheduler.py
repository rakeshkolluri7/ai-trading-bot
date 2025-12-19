# scheduler.py
import schedule
import time
import requests
from datetime import datetime

# --- CONFIGURATION ---
BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"x-api-key": "secret_mobile_key_123"}
TRADING_TIME = "16:50"  # Set this to the time you want it to run!

def run_trading_job():
    """This function runs automatically at the scheduled time."""
    print(f"\n⏰ Alarm ringing! Starting trading job at {datetime.now()}...")
    
    try:
        # 1. Ask Server to Scan
        print("   🔍 Scanning market...")
        scan_resp = requests.get(f"{BASE_URL}/scan", headers=HEADERS)
        
        if scan_resp.status_code != 200:
            print(f"   ❌ Scan Failed: {scan_resp.text}")
            return

        data = scan_resp.json()
        best_pick = data.get('best_pick')

        if best_pick:
            symbol = best_pick['symbol']
            price = best_pick['price']
            print(f"   ✅ Found Opportunity: {symbol} at ₹{price}")

            # 2. Place Trade
            print(f"   💰 Placing Order for {symbol}...")
            trade_url = f"{BASE_URL}/trade/{symbol}?action=BUY&qty=5&price={price}"
            trade_resp = requests.post(trade_url, headers=HEADERS)
            
            if trade_resp.status_code == 200:
                print("   🎉 Trade Executed Successfully!")
            else:
                print(f"   ⚠️ Trade Failed: {trade_resp.text}")
        else:
            print("   ⚠️ No good stocks found today.")

    except Exception as e:
        print(f"   ❌ Error: Is the server running? {e}")

# --- SCHEDULE SETUP ---
print(f"⏳ Scheduler Started. Waiting for {TRADING_TIME}...")

# Schedule the job every day at specific time
schedule.every().day.at(TRADING_TIME).do(run_trading_job)

# Also run it once immediately just to show it works! (Optional)
# run_trading_job() 

while True:
    schedule.run_pending()
    time.sleep(1)