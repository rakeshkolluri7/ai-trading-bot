# src/data_loader.py
import yfinance as yf
import pandas as pd
import os
import time

# Create cache directory if it doesn't exist
CACHE_DIR = "data/cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_cached_data(symbol, period):
    """Checks for fresh data (less than 15 mins old) in the cache."""
    file_path = f"{CACHE_DIR}/{symbol}_{period}.csv"
    
    if os.path.exists(file_path):
        # Check file age (15 minutes = 900 seconds)
        file_age = time.time() - os.path.getmtime(file_path)
        
        if file_age < 900: 
            # Data is fresh! Load it.
            try:
                # Read CSV and ensure index is Datetime
                df = pd.read_csv(file_path, index_col=0, parse_dates=True)
                return df
            except:
                pass # If file is corrupt, re-download
    
    return None

def save_to_cache(symbol, period, df):
    """Saves the dataframe to a CSV file."""
    file_path = f"{CACHE_DIR}/{symbol}_{period}.csv"
    try:
        df.to_csv(file_path)
    except Exception as e:
        print(f"Warning: Could not cache {symbol}: {e}")

def fetch_data(symbol, period="1mo"):
    """
    Fetches stock data with Caching.
    1. Checks Cache -> 2. Downloads from Yahoo -> 3. Saves to Cache
    """
    # 1. Try Cache First
    cached_df = get_cached_data(symbol, period)
    if cached_df is not None:
        # print(f"🚀 Cache Hit: {symbol}") # Uncomment for debugging
        return cached_df

    # 2. Download from Yahoo
    # print(f"📉 Downloading {symbol}...")
    try:
        df = yf.download(symbol, period=period, progress=False)
        
        # Flatten MultiIndex (Fixes empty charts issue)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Basic validation
        if df.empty:
            return df
            
        # 3. Save to Cache
        save_to_cache(symbol, period, df)
        
        return df
        
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return pd.DataFrame()