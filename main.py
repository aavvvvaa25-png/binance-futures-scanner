import ccxt
import pandas as pd
import time
import os
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram error: {e}", flush=True)

def get_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_trend(sym, tf, ex):
    try:
        ohlcv = ex.fetch_ohlcv(sym, tf, limit=50)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        ema20 = df['c'].ewm(span=20).mean().iloc[-1]
        ema50 = df['c'].ewm(span=50).mean().iloc[-1]
        if ema20 > ema50:
            return "BULL"
        else:
            return "BEAR"
    except:
        return "BULL"

print("KAVI BEST BOT STARTED DA! ✅ Fixed Rate Limit - Thilo Version", flush=True)
send_telegram("🚀 *KAVI BOT STARTED DA!* Scanning top 20 coins only.")

ex = ccxt.binanceusdm({'enableRateLimit': True})

while True:
    try:
        print(f"--- SCANNING STARTED ---", flush=True)
        trend = get_trend('BTC/USDT', '1h', ex)
        time.sleep(1)
        tickers=ex.fetch_tickers()
        symbols=sorted(tickers, key=lambda x: tickers[x]['quoteVolume'] if tickers[x].get('quoteVolume') else 0, reverse=True)
        symbols=[s for s in symbols if '/USDT' in s and 'UP/' not in s and 'DOWN/' not in s][:20]

        for sym in symbols:
            try:
                print(f"Checking {sym}...", flush=True)
                ohlcv=ex.fetch_ohlcv(sym, '5m', limit=100)
                time.sleep(1)
                df=pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
                close=df['c'].iloc[-1]
                vol=df['v'].iloc[-1]
                vol_avg=df['v'].rolling(20).mean().iloc[-1]
                ema20=df['c'].ewm(span=20).mean().iloc[-1]
                ema50=df['c'].ewm(span=50).mean().iloc[-1]
                rsi=get_rsi(df['c']).iloc[-1]
                res=df['h'].rolling(20).max().iloc[-2]
                sup=df['l'].rolling(20).min().iloc[-2]
                pivot=(df['h'].iloc[-2]+df['l'].iloc[-2]+df['c'].iloc[-2])/3

                long_cond = (close > res or close > pivot) and ema20 > ema50 and rsi > 55 and vol > vol_avg and trend == "BULL"
                short_cond = (close < sup or close < pivot) and ema20 < ema50 and rsi < 45 and vol > vol_avg and trend == "BEAR"

                if long_cond:
                    msg = f"🟢 *LONG SIGNAL* 🟢\nCoin: {sym}\nPrice: {close}\nRSI: {rsi:.2f}\nTrend: {trend}"
                    print(msg, flush=True)
                    send_telegram(msg)
                elif short_cond:
                    msg = f"🔴 *SHORT SIGNAL* 🔴\nCoin: {sym}\nPrice: {close}\nRSI: {rsi:.2f}\nTrend: {trend}"
                    print(msg, flush=True)
                    send_telegram(msg)

            except Exception as e:
                print(f"Error in {sym}: {e}", flush=True)
                time.sleep(2)
                continue

        print("Scan done, sleeping 60s...", flush=True)
        time.sleep(60)

    except Exception as e:
        print(f"Main loop error: {e}", flush=True)
        time.sleep(60)
