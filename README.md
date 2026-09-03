# Indian Stock Market Data Pipeline

A small batch data pipeline for NSE (National Stock Exchange of India) equities: a Python script pulls daily price data for 20 major Nifty stocks, computes day-over-day change, and persists it to SQLite. A Streamlit dashboard reads that database and renders it as a terminal-style analytics desk — top movers, gainers/losers, price comparison, market breadth, and a searchable/sortable raw data table.

## How it works

- **`ingest_stocks.py`** — fetches the last two trading days of OHLC data for the tracked tickers via `yfinance`, calculates price change and percent change, and appends the snapshot to `indian_stocks.sqlite` (table `indian_stocks`). Run it on a schedule (cron, Task Scheduler, etc.) to keep the dashboard fresh.
- **`dashboard.py`** — a Streamlit app that reads the latest snapshot per ticker from SQLite and visualizes it with Plotly: top 10 gainers/losers, price comparison across the largest names, advancing/declining breadth, and a filterable data table with CSV export.

## Setup

```bash
pip install -r requirements.txt
python ingest_stocks.py       # populates indian_stocks.sqlite
streamlit run dashboard.py    # launches the dashboard
```

## Tracked equities

20 Nifty large-caps across banking, IT, energy, auto, FMCG, and pharma — e.g. Reliance Industries, TCS, Infosys, HDFC Bank, ICICI Bank, and others (see `NIFTY_TICKERS` in `ingest_stocks.py`).

## Tech stack

Python · pandas · yfinance · SQLite · Streamlit · Plotly
