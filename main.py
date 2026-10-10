import ccxt, os, time, requests, threading
from flask import Flask
import pandas as pd

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
app = Flask(__name__)
@app.route('/')
def home(): return "Best Kavi BEST Bot Alive da!"

def send(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try: requests.post(url, data={'chat_id': CHAT_ID, 'text': text, 'parse_mode': 'Markdown'}, timeout=10)
    except: pass

def get_rsi(c, p=14):
    d=c.diff(); g=d.where(d>0,0).rolling(p).mean(); l=-d.where(d<0,0).rolling(p).mean()
    rs=g/l; return 100-(100/(1+rs))

def get_trend(symbol, tf, ex):
    try:
        ohlcv=ex.fetch_ohlcv(symbol, tf, limit=100)
        df=pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])
        e20=df['c'].ewm(span=20).mean().iloc[-1]
        e50=df['c'].ewm(span=50).mean().iloc[-1]
        if e20 > e50: return "UP"
        else: return "DOWN"
    except: return "UP"

def scanner():
    ex=ccxt.binanceusdm({'enableRateLimit': True})
    send("🤖 *BEST KAVI BEST BOT STARTED DA!*\n✅ BTC Filter + 15m Trend + SR + Pivot + EMA20/50 + RSI + VOLUME\n5m Entry + SL/TP")
    while True:
        try:
            # BEST FILTER 1: BTC TREND DA
            btc_trend = get_trend('BTC/USDT', '1h', ex)

            tickers=ex.fetch_tickers()
            symbols=sorted(tickers, key=lambda x: tickers[x]['quoteVolume'] if tickers[x].get('quoteVolume') else 0, reverse=True)
            symbols=[s for s in symbols if '/USDT' in s and 'UP/' not in s and 'DOWN/' not in s][:60]

            for sym in symbols:
                try:
                    # 5m Data
                    ohlcv=ex.fetch_ohlcv(sym, '5m', limit=220)
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

                    # BEST FILTER 2: 15m Trend
                    trend_15m = get_trend(sym, '15m', ex)
                    volume_ok = vol > (vol_avg * 1.2) # Volume strong

                    # --- BEST LONG ---
                    if (close > res or close > pivot) and ema20 > ema50 and close > ema20 and 45 < rsi < 75 and volume_ok and trend_15m=="UP" and btc_trend=="UP":
                        sl=min(sup, df['l'].rolling(10).min().iloc[-1])*0.998
                        entry=close
                        tp1=entry + (entry-sl)*1.5
                        tp2=entry + (entry-sl)*3
                        send(f"🚀 *{sym} - LONG*\nEntry: {entry}\nSL: {round(sl,5)}\nTP1: {round(tp1,5)}\nTP2: {round(tp2,5)}\nVol: {round(vol,1)} | BTC: {btc_trend} ✅")

                    # --- BEST SHORT ---
                    elif (close < sup or close < pivot) and ema20 < ema50 and close < ema20 and 25 < rsi < 55 and volume_ok and trend_15m=="DOWN" and btc_trend=="DOWN":
                        sl=max(res, df['h'].rolling(10).max().iloc[-1])*1.002
                        entry=close
                        tp1=entry - (sl-entry)*1.5
                        tp2=entry - (sl-entry)*3
                        send(f"🔻 *{sym} - SHORT*\nEntry: {entry}\nSL: {round(sl,5)}\nTP1: {round(tp1,5)}\nTP2: {round(tp2,5)}\nVol: {round(vol,1)} | BTC: {btc_trend} ✅")

                    time.sleep(0.5)
                except: continue
            time.sleep(50)
        except Exception as e: print(e); time.sleep(10)

def listener():
    offset=0
    while True:
        try:
            r=requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=10", timeout=15).json()
            for u in r.get('result',[]):
                offset=u['update_id']+1
                t=u.get('message',{}).get('text','').lower()
                if 'test' in t or '/start' in t:
                    send("🔔 *TEST OK DA THILO! BEST BOT LIVE DA!*\nBTC + 15m + 5m + Volume filter ready!\nBreakout vantha vera level signal varum da! 🚀")
        except: time.sleep(5)

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
threading.Thread(target=listener, daemon=True).start()
scanner()
