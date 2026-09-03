import sys
from datetime import datetime

import pandas as pd
import sqlite3
import yfinance as yf

DB_PATH = "indian_stocks.sqlite"   # must match dashboard.py's DB_PATH
TABLE_NAME = "indian_stocks"

print("1. Initializing NIFTY Batch Stock Ingestion Pipeline...")

NIFTY_TICKERS = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infosys",
    "HDFCBANK.NS": "HDFC Bank",
    "TATAMOTORS.NS": "Tata Motors",
    "ICICIBANK.NS": "ICICI Bank",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "ITC.NS": "ITC",
    "SBIN.NS": "State Bank of India",
    "BHARTIARTL.NS": "Bharti Airtel",
    "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "LTIM.NS": "LTIMindtree",
    "AXISBANK.NS": "Axis Bank",
    "ASIANPAINT.NS": "Asian Paints",
    "MARUTI.NS": "Maruti Suzuki",
    "TITAN.NS": "Titan Company",
    "SUNPHARMA.NS": "Sun Pharmaceutical",
    "BAJFINANCE.NS": "Bajaj Finance",
    "ULTRACEMCO.NS": "UltraTech Cement",
    "NTPC.NS": "NTPC",
}
nifty_tickers = list(NIFTY_TICKERS)

print(f"2. Fetching batch market data for {len(nifty_tickers)} NSE equities...")

try:
    data = yf.download(
        nifty_tickers, period="2d", group_by="ticker",
        progress=False, auto_adjust=True,
    )
except Exception as e:
    print(f"FATAL: batch download failed: {e}")
    sys.exit(1)

if data is None or data.empty:
    print("FATAL: no market data returned (network issue or market data unavailable).")
    sys.exit(1)

stock_records = []
ingestion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for symbol in nifty_tickers:
    try:
        ticker_df = data[symbol] if len(nifty_tickers) > 1 else data
        clean_df = ticker_df.dropna(subset=["Close"])
        if len(clean_df) < 1:
            print(f"   Skipped {symbol}: no price data")
            continue

        last_price = float(clean_df["Close"].iloc[-1])
        prev_close = float(clean_df["Close"].iloc[-2]) if len(clean_df) > 1 else last_price

        price_change = last_price - prev_close
        pct_change = (price_change / prev_close) * 100 if prev_close != 0 else 0.0

        clean_symbol = symbol.replace(".NS", "")

        stock_records.append({
            "ticker": clean_symbol,
            "company_name": NIFTY_TICKERS[symbol],
            "current_price_inr": round(last_price, 2),
            "previous_close_inr": round(prev_close, 2),
            "price_change_inr": round(price_change, 2),
            "pct_change": round(pct_change, 2),
            "ingested_at": ingestion_time,
        })

    except Exception as e:
        print(f"   Skipped {symbol}: {e}")

df_stocks = pd.DataFrame(stock_records)

if df_stocks.empty:
    print("FATAL: no records ingested; nothing written to the database.")
    sys.exit(1)

print(f"\n3. Persisting {len(df_stocks)} records into SQLite ('{DB_PATH}')...")
conn = sqlite3.connect(DB_PATH)
try:
    df_stocks.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
finally:
    conn.close()

print("\nSUCCESS! Saved NSE Stock records:")
print(df_stocks[["ticker", "current_price_inr", "pct_change", "ingested_at"]].head(5))