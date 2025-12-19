# src/config.py

# --- SYSTEM SETTINGS ---
PAPER_TRADING = True       # TRUE = Fake Money (Safe Mode), FALSE = Real Money
MOBILE_API_KEY = "secret_mobile_key_123" # Password for your App
HOST = "0.0.0.0"
PORT = 8000

# --- MARKET SETTINGS ---
DEFAULT_SYMBOL = "RELIANCE.NS" 
HISTORY_PERIOD = "2y"
INTERVAL = "1d"

# --- UPSTOX CREDENTIALS (For Real Trading) ---
ACCESS_TOKEN = "your_upstox_token_here"
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_secret"

# --- PATHS ---
MODEL_PATH = "data/models"
PAPER_TRADE_FILE = "reports/paper_trades.json"