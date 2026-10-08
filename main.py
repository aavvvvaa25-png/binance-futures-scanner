import os, time, threading, requests
import ccxt
import pandas as pd
from flask import Flask

app = Flask(__name__)
@app.route('/')
def home(): return "BOT RUNNING 24/7 - CLEAN SIGNALS"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
exchange = ccxt.binance({'enableRateLimit': True})

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID: return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
    except: pass

def get_pivot_zones(df, lookback=20):
    highs = df['h'].rolling(lookback).max()
    lows = df['l'].rolling(lookback).min()
    supply = df[df['h'] == highs].tail(3)
    demand = df[df['l'] == lows].tail(3)
    return supply, demand

def get_order_block(df):
    df['body'] = abs(df['c'] - df['o'])
    avg_body = df['body'].mean()
    bull_ob = df[(df['c'] > df['o']) & (df['body'] > avg_body)].tail(1)
    bear_ob = df[(df['c'] < df['o']) & (df['body'] > avg_body)].tail(1)
    return bull_ob, bear_ob

def scan():def scan():
    send_telegram("🚀 Thilo Bot is LIVE! Test message - if you see this, bot is working!")
    
    while True:
        try:
            tickers = exchange.fetch_tickers()
            tops = sorted([(s, t.get('quoteVolume',0)) for s,t in tickers.items() if '/USDT' in s and 'USDC' not in s], key=lambda x: x[1], reverse=True)[:50]
            for sym,_ in tops:
                try:
                    ohlcv_1h = exchange.fetch_ohlcv(sym, '1h', limit=100)
                    df1h = pd.DataFrame(ohlcv_1h, columns=['ts','o','h','l','c','v'])
                    ohlcv_15 = exchange.fetch_ohlcv(sym, '15m', limit=100)
                    df = pd.DataFrame(ohlcv_15, columns=['ts','o','h','l','c','v'])
                    df['ema50'] = df['c'].ewm(span=50).mean()
                    df['atr'] = (df['h'] - df['l']).rolling(14).mean()
                    df['vol_avg'] = df['v'].rolling(20).mean()
                    df['body'] = abs(df['c'] - df['o'])
                    last = df.iloc[-1]
                    supply_zones, demand_zones = get_pivot_zones(df1h)
                    bull_ob, bear_ob = get_order_block(df1h)
                    is_green_demand = not demand_zones.empty and last['l'] <= demand_zones['l'].max() * 1.01
                    is_red_supply = not supply_zones.empty and last['h'] >= supply_zones['h'].min() * 0.99
                    is_above_ema = last['c'] > last['ema50']
                    is_below_ema = last['c'] < last['ema50']
                    is_vol_high = last['v'] > last['vol_avg'] * 1.5
                    is_engulfing = last['c'] > last['o'] and (last['c'] - last['o']) > df['body'].mean()

                    if is_green_demand and is_above_ema and is_vol_high and is_engulfing:
                        sl = last['l'] - last['atr']
                        tp = last['c'] + (last['c'] - sl)*2
                        # CLEAN MESSAGE ONLY
                        msg = f"{sym} LONG\nEntry: {last['c']:.4f}\nSL: {sl:.4f}\nTP: {tp:.4f}"
                        send_telegram(msg)

                    if is_red_supply and is_below_ema and is_vol_high:
                        sl = last['h'] + last['atr']
                        tp = last['c'] - (sl - last['c'])*2
                        # CLEAN MESSAGE ONLY
                        msg = f"{sym} SHORT\nEntry: {last['c']:.4f}\nSL: {sl:.4f}\nTP: {tp:.4f}"
                        send_telegram(msg)

                    time.sleep(0.5)
                except: continue
        except: pass
        time.sleep(900)

threading.Thread(target=scan, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
