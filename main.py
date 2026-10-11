import requests
import time
import os

print("Bot Started - Safe Mode ON (Top 20 Breakout Scanner)")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print(f"Telegram Error: {e}")

while True:
    try:
        tickers = requests.get("https://fapi.binance.com/fapi/v1/ticker/24hr").json()
        usdt_tickers = [t for t in tickers if t['symbol'].endswith('USDT')]
        sorted_coins = sorted(usdt_tickers, key=lambda x: float(x['quoteVolume']), reverse=True)
        top_20 = sorted_coins[:20]

        print(f"Scanning Top 20: {[c['symbol'] for c in top_20]}")

        for ticker in top_20:
            symbol = ticker['symbol']
            try:
                klines = requests.get(f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=15m&limit=50").json()

                if isinstance(klines, dict) and 'code' in klines:
                    print(f"Ban Error: {klines}")
                    if klines.get('code') == -1003 or 'banned' in str(klines).lower():
                        print("IP BANNED! Waiting 10 mins...")
                        time.sleep(600)
                        break

                # ---- ANALYSIS START - BREAKOUT + VOLUME ----
                closes = [float(k[4]) for k in klines]
                volumes = [float(k[5]) for k in klines]
                highs = [float(k[2]) for k in klines]

                last_close = closes[-1]
                prev_high = max(highs[-10:-1])
                avg_vol = sum(volumes[-10:-1]) / 9

                # Condition: Price breaks 10-candle high + Volume 1.5x
                if last_close > prev_high and volumes[-1] > (avg_vol * 1.2):
                    msg = f"🚀 {symbol} BREAKOUT!\nPrice: {last_close}\nBreaks: {prev_high}\nVol: {volumes[-1]:.2f} (Avg {avg_vol:.2f})"
                    send_telegram(msg)
                    print(f"ALERT: {symbol} Breakout!")
                # ---- ANALYSIS END ----

                time.sleep(1.5)

            except Exception as e:
                print(f"Error for {symbol}: {e}")
                time.sleep(2)

        print("Round done, waiting 2 mins...")
        time.sleep(120)

    except Exception as e:
        print(f"Main Loop Error: {e}")
        time.sleep(60)
