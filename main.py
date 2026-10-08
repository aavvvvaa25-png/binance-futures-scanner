import os, time, threading, requests
import ccxt
import pandas as pd
from flask import Flask

app = Flask(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
exchange = ccxt.binance({'enableRateLimit': True})

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
    except: pass

@app.route('/')
def home(): return "BOT RUNNING - SR PIVOT OB ✅"

def get_pivot_zones(df, lookback=20):
    highs = df['h'].iloc[-lookback-5:-5].max()
    lows = df['l'].iloc[-lookback-5:-5].min()
    return highs, lows

def scan():
    send_telegram("🤖 *BOT STARTED*\n✅ SR + Pivot + Supply/Demand + Breakout")
    while True:
        try:
            for symbol in ['BTC/USDT','ETH/USDT','SOL/USDT','BNB/USDT','XRP/USDT','AVAX/USDT','DOGE/USDT']:
                ohlcv = exchange.fetch_ohlcv(symbol, '15m', limit=100)
                df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
                
                # SR + PIVOT
                supply, demand = get_pivot_zones(df, 20)
                last = df['c'].iloc[-1]
                vol = df['v'].iloc[-1]
                avg_vol = df['v'].iloc[-30:-1].mean()
                
                # Body filter for best signal
                body = abs(df['c'].iloc[-1] - df['o'].iloc[-1])
                candle_range = df['h'].iloc[-1] - df['l'].iloc[-1]
                strong = body > candle_range * 0.5

                if last > supply and vol > avg_vol*1.5 and strong:
                    send_telegram(f"🚀 *BREAKOUT LONG*\n`{symbol}`\nPivot Res: `{supply:.4f}`\nClose: `{last:.4f}`\nVol: High + Strong Body ✅")
                
                elif last < demand and vol > avg_vol*1.5 and strong:
                    send_telegram(f"🔻 *BREAKDOWN SHORT*\n`{symbol}`\nPivot Sup: `{demand:.4f}`\nClose: `{last:.4f}`\nVol: High + Strong Body ✅")
                
                time.sleep(0.5)
            time.sleep(60)
        except Exception as e:
            print(e); time.sleep(10)

if __name__ == "__main__":
    threading.Thread(target=scan, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
else:
    threading.Thread(target=scan, daemon=True).start()
