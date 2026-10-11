import os
import time
import ccxt
import pandas as pd
from flask import Flask
import threading
import requests

# ========== RENDER PORT FIX DA ==========
app = Flask(__name__)
@app.route('/')
def home():
    return "Thilo Bot LIVE! Scanning with Analysis!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
threading.Thread(target=run_web, daemon=True).start()

# ========== TELEGRAM & BINANCE ==========
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# ========== SIGNAL ANALYSIS DA - MAIN MATTER ==========
def analyze_signal(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=100)
       
