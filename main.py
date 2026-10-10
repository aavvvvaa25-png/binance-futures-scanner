from flask import Flask
from threading import Thread
import os, ccxt, pandas as pd, time, requests

app = Flask(__name__)
@app.route('/')
def home():
    return "BOT IS LIVE DA 🔥 Thilo Best!"

# --- TELEGRAM ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send(msg):
    try:
        if BOT_TOKEN and CHAT_ID:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")
    print(msg)

def get_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_trend(symbol, timeframe, ex):
    try:
        ohlcv = ex.fetch_ohlcv(symbol, timeframe, limit=50)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        ema20 = df['c'].ewm(span=20).mean().iloc[-1]
        ema50 = df['c'].ewm(span=50).mean().iloc[-1]
        return "UP" if ema20 > ema50 else "DOWN"
    except:
        return "UP"

def scanner():
    ex=ccxt.binanceusdm({'enableRateLimit': True})
    time.sleep(5)
    send("🤖 *BEST KAVI BEST BOT STARTED DA!* ✅ Fixed Rate Limit - Thilo Bot LIVE")
    while True:
        try:
            btc_trend = get_trend('BTC/USDT', '1h', ex)
            time.sleep(1)
            tickers=ex.fetch_tickers()
            symbols=sorted(tickers, key=lambda x: tickers[x]['quoteVolume'] if tickers[x].get('quoteVolume') else 0, reverse=True)
            symbols=[s for s in symbols if '/USDT' in s and 'UP/' not in s and 'DOWN/' not in s][:20]
            for sym in symbols:
                try:
                    ohlcv=ex.fetch_ohlcv(sym, '5m', limit=100)
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

                    long_cond = (close > res or close > pivot) and ema20 > ema50 and close > ema20 and 45 < rsi < 75
                    short_cond = (close < sup or close < pivot) and ema20 < ema50 and close < ema20 and 25 < rsi < 55

                    if long_cond or short_cond:
                        if vol > (vol_avg * 1.2):
                            time.sleep(1)
                            trend_15m = get_trend(sym, '15m', ex)
                            if long_cond and trend_15m=="UP" and btc_trend=="UP":
                                sl=min(sup, df['l'].rolling(10).min().iloc[-1])*0.998
                                entry=close
                                tp1=entry + (entry-sl)*1.5
                                tp2=entry + (entry-sl)*3
                                send(f"🚀 *{sym} - LONG*\nEntry: {entry}\nSL: {round(sl,5)}\nTP1: {round(tp1,5)}\nTP2: {round(tp2,5)}")
                            elif short_cond and trend_15m=="DOWN" and btc_trend=="DOWN":
                                sl=max(res, df['h'].rolling(10).max().iloc[-1])*1.002
                                entry=close
                                tp1=entry - (sl-entry)*1.5
                                tp2=entry - (sl-entry)*3
                                send(f"🔻 *{sym} - SHORT*\nEntry: {entry}\nSL: {round(sl,5)}\nTP1: {round(tp1,5)}\nTP2: {round(tp2,5)}")
                    time.sleep(2)
                except:
                    time.sleep(2)
                    continue
            time.sleep(180)
        except Exception as e:
            print(e)
            time.sleep(60)

# --- MAIN FIX ---
# Bot ah background la run pannu, Flask ah main la run pannu
Thread(target=scanner, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
