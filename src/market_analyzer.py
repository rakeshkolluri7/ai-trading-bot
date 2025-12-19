import yfinance as yf
import pandas as pd
from src.sectors import get_stocks_by_sector

# Indices to track
GLOBAL_INDICES = {
    "^NSEI": "NIFTY 50",
    "^NSEBANK": "BANK NIFTY",
    "^BSESN": "SENSEX",
    "^GSPC": "US S&P 500",
    "GC=F": "Gold",
    "CL=F": "Crude Oil"
}

def get_market_condition(df):
    """
    Classifies market condition based on Trend and Volatility.
    Returns: 'TRENDING (UP/DOWN)', 'SIDEWAYS', or 'VOLATILE'
    """
    try:
        # We need at least 50 candles
        if len(df) < 50: return "UNKNOWN"
        
        current = df.iloc[-1]
        sma_20 = df['Close'].rolling(window=20).mean().iloc[-1]
        sma_50 = df['Close'].rolling(window=50).mean().iloc[-1]
        adx = df['ADX'].iloc[-1]
        
        # 1. Check for Strong Trend (ADX > 25)
        if adx > 25:
            if current['Close'] > sma_20 > sma_50:
                return "TRENDING UP 🚀"
            elif current['Close'] < sma_20 < sma_50:
                return "TRENDING DOWN 🔻"
        
        # 2. Check for Volatility (ATR checks or huge wicks - simplified here)
        # If ADX is low (< 20), it's sideways
        if adx < 20:
            return "SIDEWAYS 💤"
            
        return "VOLATILE / CHOPPY ⚠️"
        
    except Exception as e:
        return "ERROR"

def get_global_cues():
    """
    Fetches performance of global/major indices.
    """
    cues = {}
    try:
        tickers = list(GLOBAL_INDICES.keys())
        data = yf.download(tickers, period="2d", progress=False)['Close']
        
        # Handle case where single ticker returns Series instead of DataFrame
        if isinstance(data, pd.Series):
             # Simplify if structure changes, but yf usually returns DF for multiple tickers
             pass 

        for ticker, name in GLOBAL_INDICES.items():
            if ticker in data.columns:
                prev = data[ticker].iloc[-2]
                curr = data[ticker].iloc[-1]
                change = ((curr - prev) / prev) * 100
                
                status = "NEUTRAL"
                if change > 0.5: status = "BULLISH 🟢"
                if change < -0.5: status = "BEARISH 🔴"
                
                cues[name] = {
                    "price": round(curr, 2),
                    "change": round(change, 2),
                    "status": status
                }
    except Exception as e:
        print(f"Global Cues Error: {e}")
        
    return cues

def analyze_sector_performance():
    """
    Analyzes which sectors are performing best today.
    (Simplified: Checks 1 representative stock from each sector)
    """
    sector_performance = {}
    
    # Representative stocks for quick check (User can expand this in src/sectors.py)
    # Ideally should indices (e.g., ^CNXIT, ^CNXBANK), but yfinance sometimes struggles with NSE indices
    # So we use an ETF or major stock as proxy
    sector_proxies = {
        "IT": "TCS.NS",
        "Bank": "HDFCBANK.NS",
        "Auto": "TATAMOTORS.NS",
        "Pharma": "SUNPHARMA.NS",
        "Metal": "TATASTEEL.NS",
        "FMCG": "ITC.NS"
    }

    try:
        data = yf.download(list(sector_proxies.values()), period="2d", progress=False)['Close']
        
        for sector, symbol in sector_proxies.items():
            if symbol in data.columns:
                prev = data[symbol].iloc[-2]
                curr = data[symbol].iloc[-1]
                change = ((curr - prev) / prev) * 100
                sector_performance[sector] = round(change, 2)
                
    except Exception:
        pass
        
    # Sort by performance
    sorted_sectors = sorted(sector_performance.items(), key=lambda x: x[1], reverse=True)
    return sorted_sectors
