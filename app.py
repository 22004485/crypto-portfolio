# ==========================================================
# 💹 CRYPTO PORTFOLIO SIMULATOR (Streamlit Version)
# Author: Aiman
# Description:
#   - Fetches 1-year crypto price data from Yahoo Finance
#   - Lets users pick timeframe, coins, and weight allocation
#   - Visualizes portfolio growth interactively
# ==========================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
import os

# --- CONFIG ---
TICKERS = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "XRP": "XRP-USD",
    "SOL": "SOL-USD",
    "WLD": "WLD-USD",
}
DATA_PATH = "crypto_prices.csv"

st.set_page_config(page_title="Crypto Portfolio Simulator", layout="wide")
st.title("💹 Crypto Portfolio Performance Simulator")

# --- LOAD DATA ---
@st.cache_data
def load_crypto_data():
    """Load or update crypto prices (cached for faster reload)."""
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH, parse_dates=["Date"])
        df["Date"] = pd.to_datetime(df["Date"])
        last_date = df["Date"].max().date()
        today = pd.Timestamp.today().date()

        if last_date >= today:
            return df

        new_data = yf.download(list(TICKERS.values()), start=last_date, end=today, interval="1d")["Close"]
        new_data = new_data.dropna().reset_index()
        new_data.rename(columns={v: k for k, v in TICKERS.items()}, inplace=True)

        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(DATA_PATH, index=False)
        return df

    df = yf.download(list(TICKERS.values()), period="1y", interval="1d")["Close"]
    df = df.dropna().reset_index()
    df.rename(columns={v: k for k, v in TICKERS.items()}, inplace=True)
    df.to_csv(DATA_PATH, index=False)
    return df

data = load_crypto_data()

# --- SIDEBAR SETTINGS ---
st.sidebar.header("⚙️ Settings")

investment = st.sidebar.number_input("💵 Investment Amount (USD)", min_value=100, max_value=10000, value=1000, step=100)

period = st.sidebar.selectbox("⏳ Timeframe", ["1Y", "6M", "3M"])
days_lookup = {"1Y": 365, "6M": 180, "3M": 90}
days = days_lookup[period]

selected_coins = st.sidebar.multiselect("🪙 Choose Coins", list(TICKERS.keys()), default=["BTC", "ETH", "XRP"])

weights = {}
total_weight = 0
for coin in selected_coins:
    w = st.sidebar.slider(f"{coin} Weight", 0.0, 1.0, 0.2, 0.05)
    weights[coin] = w
    total_weight += w

if total_weight == 0:
    st.warning("⚠️ Please assign non-zero weights.")
    st.stop()

# Normalize weights so they sum to 1
weights = {k: v / total_weight for k, v in weights.items()}

# --- CALCULATION ---
cutoff = pd.Timestamp.today() - timedelta(days=days)
df = data[data["Date"] >= cutoff].copy().dropna()

# Normalize prices to start = 1
for c in weights:
    df[c] = df[c] / df[c].iloc[0]

# Portfolio value
df["Portfolio"] = sum(df[c] * weights[c] for c in weights)
df["PortfolioValue"] = df["Portfolio"] * investment

# --- RESULTS ---
final_value = df["PortfolioValue"].iloc[-1]
growth = (final_value / investment - 1) * 100

st.subheader(f"💰 Portfolio Result over {period}")
st.metric("Final Value (USD)", f"${final_value:,.2f}", f"{growth:+.2f}%")

# --- PLOTLY CHART ---
fig = go.Figure()

for c in weights:
    fig.add_trace(go.Scatter(
        x=df["Date"], y=df[c] * investment,
        mode="lines", name=c, opacity=0.6
    ))

fig.add_trace(go.Scatter(
    x=df["Date"], y=df["PortfolioValue"],
    mode="lines", name="Portfolio", line=dict(color="black", width=3)
))

fig.update_layout(
    title=f"Portfolio Performance ({period})",
    xaxis_title="Date",
    yaxis_title="Value (USD)",
    template="plotly_white",
    height=500,
)

st.plotly_chart(fig, use_container_width=True)

st.caption("📈 Data source: Yahoo Finance | Built with Streamlit")

# ==========================================================
# ✅ END OF FINAL STREAMLIT VERSION
# ==========================================================
