# src/trade_executor.py
import json
import os
import datetime
import upstox_client
from upstox_client.rest import ApiException
from src.config import PAPER_TRADING, PAPER_TRADE_FILE, ACCESS_TOKEN
from src.telegram_notifier import send_telegram_alert

# Path to the balance file
BALANCE_FILE = "reports/balance.json"

def get_balance():
    if not os.path.exists(BALANCE_FILE):
        return {"initial_balance": 100000.0, "current_cash": 100000.0, "portfolio_value": 0.0, "total_equity": 100000.0}
    with open(BALANCE_FILE, 'r') as f:
        return json.load(f)

def update_balance(amount_change):
    data = get_balance()
    data["current_cash"] += amount_change
    data["total_equity"] = data["current_cash"] + data["portfolio_value"]
    
    os.makedirs(os.path.dirname(BALANCE_FILE), exist_ok=True)
    with open(BALANCE_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    return data

def execute_trade(symbol, action, quantity, price):
    timestamp = str(datetime.datetime.now())
    total_cost = quantity * price
    
    if PAPER_TRADING and action == "BUY":
        balance = get_balance()
        if balance["current_cash"] < total_cost:
            msg = f"❌ Insufficient Funds! Cash: ₹{balance['current_cash']:.2f}, Needed: ₹{total_cost:.2f}"
            send_telegram_alert(msg)
            return {"status": "Failed", "reason": "Insufficient Funds"}

    if PAPER_TRADING:
        print(f"📝 [PAPER TRADE] {action} {quantity} {symbol} @ ₹{price}")
        if action == "BUY": update_balance(-total_cost)
        elif action == "SELL": update_balance(total_cost)
            
        trade = {
            "timestamp": timestamp, "symbol": symbol, "action": action, 
            "quantity": quantity, "price": price, "total_value": total_cost
        }
        
        ledger = []
        if os.path.exists(PAPER_TRADE_FILE):
            with open(PAPER_TRADE_FILE, 'r') as f:
                try: ledger = json.load(f)
                except: pass
        
        ledger.append(trade)
        os.makedirs(os.path.dirname(PAPER_TRADE_FILE), exist_ok=True)
        with open(PAPER_TRADE_FILE, 'w') as f:
            json.dump(ledger, f, indent=4)
            
        # Send Alert
        msg = f"📝 *Paper Trade Executed*\nAction: {action}\nSymbol: `{symbol}`\nQty: {quantity}\nPrice: ₹{price}\nTotal: ₹{total_cost:.2f}"
        send_telegram_alert(msg)
            
        return {"status": "Success", "mode": "Paper", "trade": trade}

    else:
        # Live Trading
        print(f"🚨 [LIVE TRADE] Sending {action} order for {symbol} to Upstox...")
        try:
            clean_symbol = symbol.replace(".NS", "")
            instrument_key = f"NSE_EQ|{clean_symbol}"
            
            configuration = upstox_client.Configuration()
            configuration.access_token = ACCESS_TOKEN
            api_instance = upstox_client.OrderApi(upstox_client.ApiClient(configuration))
            
            order_request = upstox_client.PlaceOrderRequest(
                quantity=quantity,
                product="D", validity="DAY", price=0.0, tag="ai_bot",
                instrument_token=instrument_key, order_type="MARKET",
                transaction_type=action, disclosed_quantity=0, trigger_price=0.0, is_amo=False
            )
            
            api_response = api_instance.place_order(order_request, api_version='2.0')
            
            # Send Alert
            msg = f"🚨 *LIVE TRADE EXECUTED*\nAction: {action}\nSymbol: `{symbol}`\nQty: {quantity}\nID: `{api_response.data.order_id}`"
            send_telegram_alert(msg)
            
            return {"status": "Success", "mode": "LIVE", "order_id": api_response.data.order_id}
            
        except Exception as e:
            msg = f"❌ Trade Failed: {e}"
            send_telegram_alert(msg)
            return {"status": "Failed", "reason": str(e)}