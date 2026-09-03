"""
NSE Market Desk — Indian Stock Market Analytics
------------------------------------------------
Reads pre-ingested stock snapshots from a local SQLite database
(populated by a separate ingestion script) and renders them as a
restrained, terminal-style analytics desk.

Run with:  streamlit run dashboard.py
"""

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------
DB_PATH = "indian_stocks.sqlite"   # point this at your actual database file
TABLE_NAME = "indian_stocks"

st.set_page_config(
    page_title="NSE Market Desk",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# DESIGN TOKENS
# --------------------------------------------------------------------------
BG = "#0B0D10"
SURFACE = "#14171C"
BORDER = "#262B33"
TEXT_PRIMARY = "#E7E9EC"
TEXT_SECONDARY = "#8A93A0"
ACCENT = "#B8935A"     # muted brass — used sparingly
GAIN = "#5B8C64"       # muted sage
LOSS = "#B5544A"       # muted brick red
NEUTRAL = "#6B7280"

# --------------------------------------------------------------------------
# GLOBAL STYLE
# --------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {{
            font-family: 'IBM Plex Sans', sans-serif;
            color: {TEXT_PRIMARY};
        }}

        .stApp {{
            background-color: {BG};
        }}

        .block-container {{
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }}

        /* ---- Masthead ---- */
        .masthead {{
            border-bottom: 1px solid {BORDER};
            padding-bottom: 1.1rem;
            margin-bottom: 1.6rem;
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            flex-wrap: wrap;
        }}
        .masthead h1 {{
            font-family: 'Source Serif 4', serif;
            font-weight: 600;
            font-size: 2.1rem;
            letter-spacing: -0.01em;
            margin: 0;
            color: {TEXT_PRIMARY};
        }}
        .masthead .subtitle {{
            font-size: 0.9rem;
            color: {TEXT_SECONDARY};
            margin-top: 0.3rem;
        }}
        .masthead .timestamp {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.85rem;
            color: {TEXT_SECONDARY};
            text-align: right;
        }}

        /* ---- Ticker strip ---- */
        .ticker-strip {{
            display: flex;
            gap: 0;
            border-top: 1px solid {BORDER};
            border-bottom: 1px solid {BORDER};
            margin-bottom: 1.8rem;
            overflow-x: auto;
        }}
        .ticker-item {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.82rem;
            padding: 0.6rem 1.1rem;
            border-right: 1px solid {BORDER};
            white-space: nowrap;
        }}
        .ticker-item .sym {{ color: {TEXT_PRIMARY}; margin-right: 0.5rem; }}
        .ticker-up {{ color: {GAIN}; }}
        .ticker-down {{ color: {LOSS}; }}

        /* ---- Section headers ---- */
        .section-label {{
            font-family: 'IBM Plex Sans', sans-serif;
            font-weight: 600;
            font-size: 0.95rem;
            color: {TEXT_PRIMARY};
            border-bottom: 1px solid {BORDER};
            padding-bottom: 0.5rem;
            margin: 1.8rem 0 1rem 0;
        }}

        /* ---- KPI row ---- */
        div[data-testid="stMetric"] {{
            background-color: transparent;
            border: none;
            border-right: 1px solid {BORDER};
            border-radius: 0;
            padding: 0 1.2rem;
        }}
        div[data-testid="stMetric"]:last-child {{ border-right: none; }}
        div[data-testid="stMetricLabel"] {{
            font-size: 0.78rem;
            font-weight: 500;
            color: {TEXT_SECONDARY};
            text-transform: none;
        }}
        div[data-testid="stMetricValue"] {{
            font-family: 'IBM Plex Mono', monospace;
            font-size: 1.4rem;
            color: {TEXT_PRIMARY};
        }}

        /* ---- Dataframe ---- */
        div[data-testid="stDataFrame"] {{
            border: 1px solid {BORDER};
            border-radius: 4px;
        }}

        /* ---- Sidebar ---- */
        section[data-testid="stSidebar"] {{
            background-color: {SURFACE};
            border-right: 1px solid {BORDER};
        }}
        section[data-testid="stSidebar"] .stTextInput input,
        section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {{
            font-family: 'IBM Plex Mono', monospace;
        }}

        /* ---- Misc ---- */
        hr {{ border-color: {BORDER}; }}
        [data-testid="stCaptionContainer"] {{ color: {TEXT_SECONDARY}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

PLOTLY_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(family="IBM Plex Mono, monospace", color=TEXT_SECONDARY, size=12),
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER),
        margin=dict(l=10, r=10, t=10, b=10),
    )
)


# --------------------------------------------------------------------------
# DATA LOADING
# --------------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner="Loading latest market data...")
def load_data(db_path: str) -> pd.DataFrame:
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME};", conn)
    if df.empty:
        return df
    df["ingested_at"] = pd.to_datetime(df["ingested_at"])
    return df


def get_latest_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values("ingested_at").groupby("ticker", as_index=False).last()


# --------------------------------------------------------------------------
# LOAD
# --------------------------------------------------------------------------
try:
    df = load_data(DB_PATH)
except Exception as e:
    st.error(f"Could not load database: {e}")
    st.info(f"Run your ingestion script first to populate `{DB_PATH}`.")
    st.stop()

if df.empty:
    st.warning("No data found yet. Run your ingestion script to populate the database.")
    st.stop()

latest = get_latest_snapshot(df)

# --------------------------------------------------------------------------
# MASTHEAD
# --------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="masthead">
        <div>
            <h1>NSE Market Desk</h1>
            <div class="subtitle">Batch ingestion pipeline, SQLite storage, derived analytics</div>
        </div>
        <div class="timestamp">
            AS OF {df['ingested_at'].max():%d %b %Y &middot; %H:%M IST}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# TICKER STRIP — top movers, condensed
# --------------------------------------------------------------------------
movers = latest.reindex(latest["pct_change"].abs().sort_values(ascending=False).index).head(12)
ticker_html = '<div class="ticker-strip">'
for _, row in movers.iterrows():
    cls = "ticker-up" if row["pct_change"] >= 0 else "ticker-down"
    sign = "+" if row["pct_change"] >= 0 else ""
    ticker_html += (
        f'<div class="ticker-item"><span class="sym">{row["ticker"]}</span>'
        f'<span class="{cls}">{sign}{row["pct_change"]:.2f}%</span></div>'
    )
ticker_html += "</div>"
st.markdown(ticker_html, unsafe_allow_html=True)

# --------------------------------------------------------------------------
# SIDEBAR — filters
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("**Filters**")
    search = st.text_input("Search ticker", placeholder="RELIANCE, TCS...")
    sort_option = st.selectbox(
        "Sort table by",
        ["Most recent", "Ticker", "% change", "Price"],
    )
    st.markdown("---")
    st.caption(f"Snapshots stored: {len(df):,}")
    st.caption(f"Unique tickers: {len(latest):,}")

filtered_latest = latest.copy()
if search:
    filtered_latest = filtered_latest[
        filtered_latest["ticker"].str.contains(search, case=False, na=False)
    ]

# --------------------------------------------------------------------------
# KPI ROW
# --------------------------------------------------------------------------
gainer = latest.loc[latest["pct_change"].idxmax()]
loser = latest.loc[latest["pct_change"].idxmin()]
advancers = int((latest["pct_change"] > 0).sum())
decliners = int((latest["pct_change"] < 0).sum())

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Tracked equities", f"{len(latest):,}")
k2.metric("Top gainer", gainer["ticker"], f"{gainer['pct_change']:+.2f}%")
k3.metric("Top loser", loser["ticker"], f"{loser['pct_change']:+.2f}%")
k4.metric("Average movement", f"{latest['pct_change'].mean():+.2f}%")
k5.metric("Advancers / decliners", f"{advancers} / {decliners}")

# --------------------------------------------------------------------------
# GAINERS / LOSERS
# --------------------------------------------------------------------------
st.markdown('<div class="section-label">MOVERS</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)

with c1:
    st.caption("Top 10 gainers")
    top_gainers = latest.sort_values("pct_change", ascending=False).head(10)
    fig_g = go.Figure(
        go.Bar(
            x=top_gainers["pct_change"],
            y=top_gainers["ticker"],
            orientation="h",
            marker_color=GAIN,
            text=[f"{v:+.2f}%" for v in top_gainers["pct_change"]],
            textposition="outside",
        )
    )
    fig_g.update_layout(template=PLOTLY_TEMPLATE, height=340, xaxis_title=None, yaxis_title=None)
    fig_g.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_g, use_container_width=True, config={"displayModeBar": False})

with c2:
    st.caption("Top 10 losers")
    top_losers = latest.sort_values("pct_change", ascending=True).head(10)
    fig_l = go.Figure(
        go.Bar(
            x=top_losers["pct_change"],
            y=top_losers["ticker"],
            orientation="h",
            marker_color=LOSS,
            text=[f"{v:+.2f}%" for v in top_losers["pct_change"]],
            textposition="outside",
        )
    )
    fig_l.update_layout(template=PLOTLY_TEMPLATE, height=340, xaxis_title=None, yaxis_title=None)
    fig_l.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_l, use_container_width=True, config={"displayModeBar": False})

# --------------------------------------------------------------------------
# VALUATION + BREADTH
# --------------------------------------------------------------------------
st.markdown('<div class="section-label">VALUATION &amp; BREADTH</div>', unsafe_allow_html=True)
c3, c4 = st.columns([1.4, 1])

with c3:
    st.caption("Price comparison, top 15 by value (INR)")
    top_by_price = latest.sort_values("current_price_inr", ascending=False).head(15)
    fig_v = go.Figure(
        go.Bar(
            x=top_by_price["ticker"],
            y=top_by_price["current_price_inr"],
            marker_color=ACCENT,
            text=[f"₹{v:,.0f}" for v in top_by_price["current_price_inr"]],
            textposition="outside",
        )
    )
    fig_v.update_layout(template=PLOTLY_TEMPLATE, height=340, xaxis_title=None, yaxis_title="INR")
    st.plotly_chart(fig_v, use_container_width=True, config={"displayModeBar": False})

with c4:
    st.caption("Market breadth")
    unchanged = len(latest) - advancers - decliners
    fig_b = go.Figure(
        go.Bar(
            x=["Advancing", "Declining", "Unchanged"],
            y=[advancers, decliners, unchanged],
            marker_color=[GAIN, LOSS, NEUTRAL],
            text=[advancers, decliners, unchanged],
            textposition="outside",
        )
    )
    fig_b.update_layout(template=PLOTLY_TEMPLATE, height=340, xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig_b, use_container_width=True, config={"displayModeBar": False})

# --------------------------------------------------------------------------
# DATA TABLE
# --------------------------------------------------------------------------
st.markdown('<div class="section-label">RAW DATA</div>', unsafe_allow_html=True)

sort_map = {
    "Most recent": ("ingested_at", False),
    "Ticker": ("ticker", True),
    "% change": ("pct_change", False),
    "Price": ("current_price_inr", False),
}
sort_col, sort_asc = sort_map[sort_option]

display_df = df.copy()
if search:
    display_df = display_df[display_df["ticker"].str.contains(search, case=False, na=False)]
display_df = display_df.sort_values(sort_col, ascending=sort_asc)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "pct_change": st.column_config.NumberColumn("% change", format="%.2f%%"),
        "current_price_inr": st.column_config.NumberColumn("Price (INR)", format="₹%.2f"),
        "ingested_at": st.column_config.DatetimeColumn("Ingested at", format="DD MMM YYYY, HH:mm"),
    },
)

st.download_button(
    "Download filtered data (CSV)",
    data=display_df.to_csv(index=False).encode("utf-8"),
    file_name="nse_stock_data.csv",
    mime="text/csv",
)