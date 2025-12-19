# src/portfolio.py
import json
import os
from src.config import PAPER_TRADE_FILE
from src.data_loader import fetch_data
from src.trade_executor import execute_trade

def get_open_positions():
    """Reads the ledger and figures out what we currently own."""
    if not os.path.exists(PAPER_TRADE_FILE):
        return {}
    
    with open(PAPER_TRADE_FILE, 'r') as f:
        trades = json.load(f)
    
    holdings = {}
    
    # Calculate net quantity for each stock
    for t in trades:
        sym = t['symbol']
        qty = t['quantity']
        action = t['action']
        
        if sym not in holdings:
            holdings[sym] = {"qty": 0, "last_buy_price": 0}
        
        if action == "BUY":
            holdings[sym]["qty"] += qty
            holdings[sym]["last_buy_price"] = t['price'] # Update buy price
        elif action == "SELL":
            holdings[sym]["qty"] -= qty
            
    # Filter out stocks where we have 0 quantity (already sold)
    return {k: v for k, v in holdings.items() if v["qty"] > 0}

def check_for_exits():
    """Checks if we should sell any stocks based on Profit/Loss."""
    print("💼 Checking Portfolio for Exits...")
    portfolio = get_open_positions()
    messages = []
    
    for symbol, data in portfolio.items():
        qty = data["qty"]
        buy_price = data["last_buy_price"]
        
        # Get current market price
        try:
            df = fetch_data(symbol, period="1d")
            if df.empty: continue
            current_price = float(df['Close'].iloc[-1])
        except:
            continue
            
        # Calculate Profit/Loss %
        pnl_percent = ((current_price - buy_price) / buy_price) * 100
        
        print(f"   Checking {symbol}: Bought @ {buy_price}, Now @ {current_price} ({pnl_percent:.2f}%)")
        
        # --- RULES FOR SELLING ---
        # 1. Take Profit: If we made more than 2% profit
        # 2. Stop Loss: If we lost more than 1%
        if pnl_percent >= 2.0:
            reason = "TARGET HIT 🎯"
            execute_trade(symbol, "SELL", qty, current_price)
            messages.append(f"Sold {symbol}: {reason}")
            
        elif pnl_percent <= -1.0:
            reason = "STOP LOSS 🛑"
            execute_trade(symbol, "SELL", qty, current_price)
            messages.append(f"Sold {symbol}: {reason}")
            
    if not messages:
        return "No sells needed."
    return messages