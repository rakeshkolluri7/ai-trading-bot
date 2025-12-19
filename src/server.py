# src/server.py
from src.portfolio import check_for_exits
from src.trade_executor import execute_trade, get_balance
from fastapi import FastAPI, Header, HTTPException
from src.config import MOBILE_API_KEY, PAPER_TRADE_FILE
from src.scanner import scan_market, analyze_single_stock
from src.trade_executor import execute_trade
from src.utils import ensure_directories_exist
from src.sectors import SECTOR_MAP
import json
import os

app = FastAPI()

def verify_key(x_api_key: str = Header(None)):
    if x_api_key != MOBILE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

@app.on_event("startup")
def startup_event():
    ensure_directories_exist()

@app.get("/")
def home(): return {"message": "AI Trading Bot is Online 🤖"}

@app.get("/scan")
def run_scan(sector: str = "All", x_api_key: str = Header(None)):
    verify_key(x_api_key)
    best, full_report = scan_market(sector)
    return {"best_pick": best, "market_data": full_report}

@app.get("/analyze/{symbol}")
def analyze_stock(symbol: str, x_api_key: str = Header(None)):
    verify_key(x_api_key)
    # Ensure symbol has .NS extension if missing
    if not symbol.endswith(".NS") and not symbol.endswith(".BO"):
        symbol += ".NS"
    report = analyze_single_stock(symbol)
    return report

@app.get("/sectors")
def get_sectors():
    return {"sectors": list(SECTOR_MAP.keys())}

@app.post("/trade/{symbol}")
def place_trade(symbol: str, action: str, qty: int, price: float, stop_loss: float = 0.0, target: float = 0.0, x_api_key: str = Header(None)):
    verify_key(x_api_key)
    result = execute_trade(symbol, action, qty, price, stop_loss, target)
    return result

@app.post("/propose")
def propose_trade(trade: dict, x_api_key: str = Header(None)):
    verify_key(x_api_key)
    from src.telegram_notifier import send_trade_proposal
    send_trade_proposal(trade)
    return {"status": "Proposal Sent"}

@app.get("/ledger")
def get_history(x_api_key: str = Header(None)):
    verify_key(x_api_key)
    if os.path.exists(PAPER_TRADE_FILE):
        with open(PAPER_TRADE_FILE, 'r') as f: return json.load(f)
    return []

@app.get("/balance")
def get_account_balance(x_api_key: str = Header(None)):
    verify_key(x_api_key)
    return get_balance()

@app.get("/check-exits")
def trigger_exits(x_api_key: str = Header(None)):
    verify_key(x_api_key)
    result = check_for_exits()
    return {"status": "checked", "actions": result}

from src.trade_executor import approve_order, reject_order

@app.get("/trade/pending")
def start_pending_trades(x_api_key: str = Header(None)):
    verify_key(x_api_key)
    if os.path.exists("data/pending_orders.json"):
        with open("data/pending_orders.json", 'r') as f: return json.load(f)
    return []

@app.post("/trade/approve/{order_id}")
def approve_pending_trade(order_id: str, x_api_key: str = Header(None)):
    verify_key(x_api_key)
    start_time = os.path.getmtime("data/pending_orders.json")
    success = approve_order(order_id)
    if success: return {"status": "Approved and Executed"}
    return {"status": "Failed", "detail": "Order not found"}

@app.post("/trade/reject/{order_id}")
def reject_pending_trade(order_id: str, x_api_key: str = Header(None)):
    verify_key(x_api_key)
    success = reject_order(order_id)
    if success: return {"status": "Rejected"}
    return {"status": "Failed", "detail": "Order not found"}