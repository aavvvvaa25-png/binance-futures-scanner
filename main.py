import os, time, requests, threading
from flask import Flask
import pandas as pd
import ccxt

app = Flask(__name__)
@app.route('/')
def home():
    return "Bot Running 24/7"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'future'}})

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def scan():
    while True:
        try:
            tickers = exchange.fetch_tickers()
            tops = sorted([(s,t.get('quoteVolume',0)) for s,t in tickers.items() if '/USDT' in s], key=lambda x:x[1], reverse=True)[:40]
            for sym,_ in tops:
                try:
                    ohlcv = exchange.fetch_ohlcv(sym, '15m', limit=100)
                    df = pd.DataFrame(ohlcv, columns=['ts','o','h','l','c','v'])
                    df['ema50'] = df['c'].ewm(span=50).mean()
                    last = df.iloc[-1]
                    if last['c'] > last['o'] and last['c'] > last['ema50']:
                        send_telegram(f"LONG {sym} Entry:{last['c']} SL:{last['l']}")
                    time.sleep(0.3)
                except: continue
        except: pass
        time.sleep(900)

threading.Thread(target=scan, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
