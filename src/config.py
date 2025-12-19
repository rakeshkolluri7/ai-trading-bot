# src/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- SYSTEM SETTINGS ---
PAPER_TRADING = True       # Set to False for REAL MONEY
MOBILE_API_KEY = os.getenv("MOBILE_API_KEY")
HOST = "0.0.0.0"
PORT = 8000

# --- MARKET SETTINGS ---
DEFAULT_SYMBOL = "RELIANCE.NS"
HISTORY_PERIOD = "2y"
INTERVAL = "1d"

# --- UPSTOX CREDENTIALS ---
ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN")
CLIENT_ID = os.getenv("UPSTOX_CLIENT_ID")
CLIENT_SECRET = os.getenv("UPSTOX_CLIENT_SECRET")

# --- TELEGRAM CREDENTIALS ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# --- PATHS ---
MODEL_PATH = "data/models"
PAPER_TRADE_FILE = "reports/paper_trades.json"