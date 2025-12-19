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

        # STEP 1: SELL (Risk Management) - ENABLED NOW
        print("   💼 Checking Portfolio for Exits...")
        exit_resp = requests.get(f"{BASE_URL}/check-exits", headers=HEADERS)
        if exit_resp.status_code == 200:
             print(f"   📉 Exits: {exit_resp.json().get('actions')}")
             
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

            # 2. Propose Trade (Human-in-the-Loop)
            print(f"   📢 Sending Proposal for {symbol}...")
            
            # Construct Proposal Data
            proposal = {
                "symbol": symbol,
                "current_price": best_pick['price'],
                "trade_type": best_pick['trade_type'],
                "stop_loss": best_pick.get('stop_loss', 0), # Scanner doesn't return this yet in list, need to verify
                "target": best_pick.get('target', 0),
                "risk_reward": best_pick.get('risk_reward', 'N/A'),
                "conf_score": best_pick['score'],
                "reason": best_pick['reasons'],
                "market_condition": best_pick.get('patterns', 'N/A')
            }
            
            # Ideally scanner scan should return full details.
            # For now, we trust the 'best_pick' has enough or we trigger analyze again.
            # Let's just send what we have.
            
            requests.post(f"{BASE_URL}/propose", json=proposal, headers=HEADERS)
             
            print("   📨 Proposal Sent to Telegram!")
            # trade_url = f"{BASE_URL}/trade/{symbol}?action=BUY&qty=5&price={price}"
            # trade_resp = requests.post(trade_url, headers=HEADERS)
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