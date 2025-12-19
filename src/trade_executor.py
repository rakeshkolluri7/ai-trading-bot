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

def execute_trade(symbol, action, quantity, price, stop_loss=0.0, target=0.0, bypass_approval=False):
    timestamp = str(datetime.datetime.now())
    
    # --- RISK MANAGEMENT & POSITION SIZING ---
    balance = get_balance()
    MAX_RISK_PER_TRADE_PCT = 0.02 # 2% Capital at risk
    
    # Verify Funds (Paper Trade)
    if PAPER_TRADING and action == "BUY":
        total_cost = quantity * price
        if balance["current_cash"] < total_cost:
             msg = f"❌ *Trade Rejected*: Insufficient Funds! Req: ₹{total_cost}"
             send_telegram_alert(msg)
             return {"status": "Failed", "reason": "Insufficient Funds"}

    # --- HUMAN IN THE LOOP ---
    # Default to requiring approval unless explicitly forced
    REQUIRE_APPROVAL = True 
    PENDING_ORDERS_FILE = "data/pending_orders.json"

    if REQUIRE_APPROVAL and not bypass_approval:
        print(f"✋ [APPROVAL NEEDED] Trade for {symbol} halted for user review.")
        
        pending_trade = {
            "id": f"ord_{int(datetime.datetime.now().timestamp())}",
            "timestamp": timestamp,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "price": price,
            "stop_loss": stop_loss,
            "target": target,
            "status": "WAITING_APPROVAL"
        }
        
        # Save to Pending File
        existing_orders = []
        if os.path.exists(PENDING_ORDERS_FILE):
             with open(PENDING_ORDERS_FILE, 'r') as f:
                 try: existing_orders = json.load(f)
                 except: pass
        
        existing_orders.append(pending_trade)
        os.makedirs(os.path.dirname(PENDING_ORDERS_FILE), exist_ok=True)
        with open(PENDING_ORDERS_FILE, 'w') as f:
            json.dump(existing_orders, f, indent=4)
            
        # Send Telegram Approval Request
        msg = f"""
⚠️ *APPROVAL REQUIRED*
---------------------
*Action:* {action} {symbol}
*Qty:* {quantity} @ ₹{price}
*Reason:* AI Strategy Signal

_Open Dashboard to Approve_
        """
        send_telegram_alert(msg)
        
        return {"status": "Pending", "message": "Trade paused for approval", "order_id": pending_trade['id']}

    # --- EXECUTION (Real or Paper) ---
    if PAPER_TRADING:
        print(f"📝 [PAPER TRADE] {action} {quantity} {symbol} @ ₹{price}")
        
        if action == "BUY": 
            update_balance(-quantity * price)
        elif action == "SELL": 
            update_balance(quantity * price)
            
        trade = {
            "timestamp": timestamp, "symbol": symbol, "action": action, 
            "quantity": quantity, "price": price, 
            "total_value": quantity * price,
            "stop_loss": stop_loss,
            "target": target,
            "status": "OPEN"
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
        msg = f"""
✅ *EXECUTION CONFIRMED ({'PAPER' if PAPER_TRADING else 'LIVE'})*
--------------------------
*Symbol:* `{symbol}`
*Action:* {action}
*Qty:* {quantity}
*Price:* ₹{price}
*Stop Loss:* {stop_loss}
*Target:* {target}
        """
        send_telegram_alert(msg)
            
        return {"status": "Success", "mode": "Paper", "trade": trade}

    else:
        # Live Trading (Upstox)
        print(f"🚨 [LIVE TRADE] Sending {action} order for {symbol} to Upstox...")
        try:
            clean_symbol = symbol.replace(".NS", "")
            instrument_key = f"NSE_EQ|{clean_symbol}"
            
            configuration = upstox_client.Configuration()
            configuration.access_token = ACCESS_TOKEN
            api_instance = upstox_client.OrderApi(upstox_client.ApiClient(configuration))
            
            # Main Order (Market)
            order_request = upstox_client.PlaceOrderRequest(
                quantity=quantity,
                product="D", validity="DAY", price=0.0, tag="ai_bot",
                instrument_token=instrument_key, order_type="MARKET",
                transaction_type=action, disclosed_quantity=0, trigger_price=0.0, is_amo=False
            )
            api_response = api_instance.place_order(order_request, api_version='2.0')
            
            msg = f"🚨 *LIVE TRADE EXECUTED*\nAction: {action}\nSymbol: `{symbol}`\nQty: {quantity}\nSL: {stop_loss}\nTarget: {target}"
            send_telegram_alert(msg)
            
            return {"status": "Success", "mode": "LIVE", "order_id": api_response.data.order_id}
            
        except Exception as e:
            msg = f"❌ Trade Failed: {e}"
            send_telegram_alert(msg)
            return {"status": "Failed", "reason": str(e)}

def approve_order(order_id):
    """Executes a previously pending order by bypassing approval."""
    PENDING_ORDERS_FILE = "data/pending_orders.json"
    
    if not os.path.exists(PENDING_ORDERS_FILE): return False
    
    with open(PENDING_ORDERS_FILE, 'r') as f: orders = json.load(f)
    
    target_order = None
    new_list = []
    
    for o in orders:
        if o['id'] == order_id: target_order = o
        else: new_list.append(o)
        
    if target_order:
        # Save trimmed list (removed the approved order)
        with open(PENDING_ORDERS_FILE, 'w') as f: json.dump(new_list, f, indent=4)
        
        # Execute actual trade with bypass_approval=True
        print(f"✅ Approving Order {order_id}")
        return execute_trade(
            symbol=target_order['symbol'],
            action=target_order['action'],
            quantity=target_order['quantity'],
            price=target_order['price'],
            stop_loss=target_order.get('stop_loss', 0.0),
            target=target_order.get('target', 0.0),
            bypass_approval=True
        )
    return False

def reject_order(order_id):
    """Removes a pending order without executing it."""
    PENDING_ORDERS_FILE = "data/pending_orders.json"
    
    if not os.path.exists(PENDING_ORDERS_FILE): return False
    
    with open(PENDING_ORDERS_FILE, 'r') as f: orders = json.load(f)
    
    new_list = [o for o in orders if o['id'] != order_id]
    
    if len(new_list) < len(orders):
        with open(PENDING_ORDERS_FILE, 'w') as f: json.dump(new_list, f, indent=4)
        print(f"❌ Order {order_id} Rejected")
        return True
    return False