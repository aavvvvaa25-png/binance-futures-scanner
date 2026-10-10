from flask import Flask
from threading import Thread
import os, ccxt, pandas as pd, time
import pandas_ta as ta

app = Flask(__name__)
@app.route('/')
def home():
    return "BOT IS LIVE DA"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

Thread(target=run_web, daemon=True).start()


def scanner():
    ex=ccxt.binanceusdm({'enableRateLimit': True})
    send("🤖 *BEST KAVI BEST BOT STARTED DA!* ✅ Fixed Rate Limit")
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
                        volume_ok = vol > (vol_avg * 1.2)
                        if volume_ok:
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
        except Exception as e: print(e); time.sleep(60)
