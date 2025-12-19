# src/sectors.py

# INSTITUTIONAL SECTOR WATCHLIST (High Liquidity NSE Stocks)
SECTOR_MAP = {
    "NIFTY_BANK": [
        "HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS", "KOTAKBANK.NS", 
        "INDUSINDBK.NS", "BANKBARODA.NS", "PNB.NS", "IDFCFIRSTB.NS", "AUBANK.NS"
    ],
    "NIFTY_IT": [
        "TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS", 
        "LTIM.NS", "PERSISTENT.NS", "COFORGE.NS", "MPHASIS.NS", "LTTS.NS"
    ],
    "NIFTY_AUTO": [
        "TATAMOTORS.NS", "M&M.NS", "MARUTI.NS", "BAJAJ-AUTO.NS", "EICHERMOT.NS", 
        "HEROMOTOCO.NS", "TVSMOTOR.NS", "ASHOKLEY.NS", "BHARATFORG.NS", "MOTHERSON.NS"
    ],
    "NIFTY_ENERGY": [
        "RELIANCE.NS", "NTPC.NS", "ONGC.NS", "POWERGRID.NS", "BPCL.NS", 
        "COALINDIA.NS", "IOC.NS", "GAIL.NS", "ADANIGREEN.NS", "TATAPOWER.NS"
    ],
    "NIFTY_FMCG": [
        "ITC.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "BRITANNIA.NS", "TATACONSUM.NS", 
        "DABUR.NS", "GODREJCP.NS", "MARICO.NS", "VARUN.NS", "COLPAL.NS"
    ],
    "NIFTY_PHARMA": [
        "SUNPHARMA.NS", "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS", 
        "LUPIN.NS", "AUROPHARMA.NS", "ALKEM.NS", "TORNTPHARM.NS", "ZYDUSLIFE.NS"
    ],
    "NIFTY_METAL": [
        "TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "VEDL.NS", "SAIL.NS", 
        "JINDALSTEL.NS", "NMDC.NS", "NATIONALUM.NS", "ADANIENT.NS"
    ],
    "NIFTY_REALTY": [
        "DLF.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PHOENIXLTD.NS", "PRESTIGE.NS"
    ]
}

def get_sector_list():
    return list(SECTOR_MAP.keys())

def get_stocks_by_sector(sector_name):
    if sector_name == "All":
        all_stocks = []
        for stocks in SECTOR_MAP.values():
            all_stocks.extend(stocks)
        return list(set(all_stocks)) # Remove duplicates
    return SECTOR_MAP.get(sector_name, [])