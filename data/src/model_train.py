# src/model_train.py
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import pandas as pd
import ta
import time
from src.data_loader import fetch_data
from src.config import MODEL_PATH
from src.utils import ensure_directories_exist
from src.sectors import get_sector_list, get_stocks_by_sector

def train_model(symbol):
    print(f"🧠 Training AI Brain for {symbol}...")
    try:
        # 1. Fetch Data (2 years is good for pattern recognition)
        df = fetch_data(symbol, period="2y")
        
        # Need enough data to calculate indicators (at least ~50-60 rows)
        if df.empty or len(df) < 60: 
            print(f"   ⚠️ Not enough data for {symbol}. Skipping.")
            return

        # 2. Indicators (Must match scanner.py exactly)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
        
        # 3. Target: 1 if Price rises tomorrow, else 0
        df['Target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        
        df.dropna(inplace=True)

        features = ['RSI', 'SMA_20', 'SMA_50', 'Close', 'Volume']
        X = df[features]
        y = df['Target']

        # 4. Train
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)

        # 5. Save
        ensure_directories_exist()
        clean_symbol = symbol.replace('.NS', '')
        save_path = f"{MODEL_PATH}/{clean_symbol}_model.pkl"
        joblib.dump(model, save_path)
        print(f"   ✅ Saved {clean_symbol}")
        
    except Exception as e:
        print(f"   ❌ Failed {symbol}: {e}")

if __name__ == "__main__":
    print("🚀 Starting Mass Training for ALL Sectors...")
    
    # Get every single stock from your new sector map
    all_sectors = get_sector_list()
    all_stocks = []
    for sector in all_sectors:
        stocks = get_stocks_by_sector(sector)
        all_stocks.extend(stocks)
    
    # Remove duplicates (some stocks might be in multiple lists)
    unique_stocks = list(set(all_stocks))
    
    print(f"📋 Found {len(unique_stocks)} unique stocks to train.")
    
    for i, stock in enumerate(unique_stocks):
        print(f"[{i+1}/{len(unique_stocks)}]", end=" ")
        train_model(stock)
        time.sleep(1) # Be polite to the API
        
    print("🏁 All Brains Trained!")