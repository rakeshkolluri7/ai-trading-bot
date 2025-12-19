# src/calculator.py

def calculate_delivery_costs(price, qty, action="BUY"):
    """
    Calculates charges for Indian Equity Delivery.
    """
    turnover = price * qty
    
    # 1. Brokerage (Upstox/Zerodha usually 0 or 20, let's assume 20 flat or 0.1%)
    # Using 0.1% or max 20 logic
    brokerage = min(20, turnover * 0.001)
    
    # 2. STT (Securities Transaction Tax) - 0.1% on Buy & Sell
    stt = turnover * 0.001
    
    # 3. Exchange Transaction Charges (NSE) - 0.00345%
    exchange_charges = turnover * 0.0000345
    
    # 4. SEBI Turnover Fees - 0.0001%
    sebi_charges = turnover * 0.000001
    
    # 5. Stamp Duty - 0.015% (Only on Buy)
    stamp_duty = turnover * 0.00015 if action == "BUY" else 0
    
    # 6. GST - 18% on (Brokerage + Exchange + SEBI)
    gst = (brokerage + exchange_charges + sebi_charges) * 0.18
    
    total_tax = brokerage + stt + exchange_charges + sebi_charges + stamp_duty + gst
    
    # Break-even calculation
    break_even_price = (turnover + total_tax) / qty if action == "BUY" else (turnover - total_tax) / qty
    
    return {
        "turnover": round(turnover, 2),
        "brokerage": round(brokerage, 2),
        "stt": round(stt, 2),
        "total_charges": round(total_tax, 2),
        "net_price": round(break_even_price, 2),
        "points_to_breakeven": round(total_tax / qty, 2)
    }