# test_app.py
import requests
import time

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"x-api-key": "secret_mobile_key_123"}

def run_test():
    print("📱 --- MOBILE APP SIMULATION ---")
    
    # 1. Ask Bot to Scan
    print("🔍 Requesting Market Scan...")
    resp = requests.get(f"{BASE_URL}/scan", headers=HEADERS)
    
    if resp.status_code != 200:
        print(f"❌ Scan Failed: {resp.text}")
        return

    data = resp.json()
    best_pick = data.get('best_pick')

    if best_pick:
        symbol = best_pick['symbol']
        price = best_pick['price']
        print(f"✅ Bot Recommends: {symbol} at ₹{price}")

        # 2. PLACE THE TRADE (The New Part!)
        print(f"💰 Buying 10 shares of {symbol}...")
        
        # We send a POST request to tell the robot to BUY
        trade_url = f"{BASE_URL}/trade/{symbol}?action=BUY&qty=10&price={price}"
        trade_resp = requests.post(trade_url, headers=HEADERS)
        
        if trade_resp.status_code == 200:
            print("   🎉 Trade Successful!")
        else:
            print(f"   ⚠️ Trade Failed: {trade_resp.text}")

    else:
        print("⚠️ No good stocks found today.")
    
    # 3. Check Ledger (Now it should show the trade!)
    print("\n📜 Checking Trade History...")
    ledger_resp = requests.get(f"{BASE_URL}/ledger", headers=HEADERS)
    print(ledger_resp.json())

if __name__ == "__main__":
    time.sleep(1)
    run_test()