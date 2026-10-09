import ccxt, os, time, requests, threading
from flask import Flask
import pandas as pd

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
app = Flask(__name__)
@app.route('/')
def home(): return "Best Kavi ATR Major Only Alive!"

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
        return "UP" if e20 > e50 else "DOWN"
    except: return "UP"

def scanner():
    ex=ccxt.binance()
    send("🤖 *BEST KAVI ATR MAJOR BOT STARTED DA!*\n✅ ATR SL + No W/USDC + Major Only")
    BLACKLIST = ['W/USDT','USDC/USDT','MSTRB/USDT','SPCXB/USDT','SNDKB/USDT','USDE/USDT','FDUSD/USDT','TUSD/USDT']
    while True:
        try:
            btc_trend = get_trend('BTC/USDT', '1h', ex)
            major_coins = ['BTC/USDT','ETH/USDT','SOL/USDT','BNB/USDT','XRP/USDT','ADA/USDT','DOGE/USDT','AVAX/USDT','DOT/USDT','LINK/USDT','LTC/USDT','BCH/USDT','UNI/USDT','XLM/USDT','ETC/USDT','FIL/USDT','APT/USDT','ARB/USDT','OP/USDT','INJ/USDT','SUI/USDT','SEI/USDT','TIA/USDT','NEAR/USDT','MATIC/USDT','ATOM/USDT','AAVE/USDT','STX/USDT','PEPE/USDT','SHIB/USDT']
            for sym in major_coins:
                if sym in BLACKLIST: continue
                try:
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
                    atr=(df['h']-df['l']).rolling(14).mean().iloc[-1]

                    trend_15m = get_trend(sym, '15m', ex)
                    volume_ok = vol > (vol_avg * 1.3)

                    if (close > res or close > pivot) and ema20 > ema50 and close > ema20 and 45 < rsi < 75 and volume_ok and trend_15m=="UP" and btc_trend=="UP":
                        sl = close - (atr * 1.8)
                        if sl < sup: sl = sup * 0.998
                        tp1 = close + (close - sl)*1.5
                        tp2 = close + (close - sl)*3
                        send(f"🚀 *{sym} - LONG*\nEntry: {close}\nSL: {round(sl,5)}\nTP1: {round(tp1,5)}\nTP2: {round(tp2,5)}\nVol: {round(vol,1)} | BTC: {btc_trend} ✅")
                    elif (close < sup or close < pivot) and ema20 < ema50 and close < ema20 and 25 < rsi < 55 and volume_ok and trend_15m=="DOWN" and btc_trend=="DOWN":
                        sl = close + (atr * 1.8)
                        if sl > res: sl = res * 1.002
                        tp1 = close - (sl - close)*1.5
                        tp2 = close - (sl - close)*3
                        send(f"🔻 *{sym} - SHORT*\nEntry: {close}\nSL: {round(sl,5)}\nTP1: {round(tp1,5)}\nTP2: {round(tp2,5)}\nVol: {round(vol,1)} | BTC: {btc_trend} ✅")
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
                    send("🔔 *TEST OK DA THILO! MAJOR ATR BOT LIVE DA!* W/USDC varathu da ✅")
        except: time.sleep(5)

threading.Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
threading.Thread(target=listener, daemon=True).start()
scanner()
