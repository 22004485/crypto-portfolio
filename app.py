# ==========================================================
# 💹 CRYPTO PORTFOLIO SIMULATOR (Portfolio Line Only)
# Author: Aiman
# ==========================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Crypto Portfolio Simulator", layout="wide")

st.title("💹 Crypto Portfolio Performance Simulator")

# --- CONFIG ---
TICKERS = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "XRP": "XRP-USD",
    "SOL": "SOL-USD",
    "WLD": "WLD-USD",
}

DATA_PATH = "crypto_prices.csv"

# --- LOAD DATA ---
@st.cache_data
def load_data():
    """Load or update 1-year crypto data."""
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH, parse_dates=["Date"])
        df["Date"] = pd.to_datetime(df["Date"])

        last_date = df["Date"].max().date()
        today = pd.Timestamp.today().date()

        if last_date >= today:
            return df

        # fetch new data
        new_df = yf.download(
            list(TICKERS.values()),
            start=pd.Timestamp(last_date),
            end=pd.Timestamp(today),
            interval="1d"
        )["Close"]

        new_df = new_df.dropna().reset_index()
        new_df.rename(columns={v: k for k, v in TICKERS.items()}, inplace=True)

        df = pd.concat([df, new_df], ignore_index=True)
        df.to_csv(DATA_PATH, index=False)
        return df

    # fresh download
    df = yf.download(list(TICKERS.values()), period="1y", interval="1d")["Close"]
    df = df.dropna().reset_index()
    df.rename(columns={v: k for k, v in TICKERS.items()}, inplace=True)
    df.to_csv(DATA_PATH, index=False)
    return df


data = load_data()

# --- SIDEBAR ---
st.sidebar.header("⚙️ Settings")

investment = st.sidebar.number_input(
    "💵 Investment Amount (USD)",
    min_value=100, max_value=10000, value=1000, step=100
)

period = st.sidebar.selectbox("⏳ Timeframe", ["1Y", "6M", "3M"])
days_lookup = {"1Y": 365, "6M": 180, "3M": 90}

selected_coins = st.sidebar.multiselect(
    "🪙 Choose Coins",
    list(TICKERS.keys()),
    default=["BTC", "ETH", "XRP"]
)

weights = {}
total_weight = 0
for coin in selected_coins:
    w = st.sidebar.slider(f"{coin} Weight", 0.0, 1.0, 0.2, 0.05)
    weights[coin] = w
    total_weight += w

# Normalize weights
if total_weight == 0:
    st.warning("⚠️ Please assign at least one weight.")
    st.stop()

weights = {k: v / total_weight for k, v in weights.items()}

# --- FILTER DATA ---
cutoff = pd.Timestamp.today() - timedelta(days=days_lookup[period])
df = data[data["Date"] >= cutoff].copy().dropna()

# --- PORTFOLIO CALC ---
for c in weights:
    df[c] = df[c] / df[c].iloc[0]

df["PortfolioIndex"] = sum(df[c] * weights[c] for c in weights)
df["PortfolioValue"] = df["PortfolioIndex"] * investment

final_value = df["PortfolioValue"].iloc[-1]
growth = (final_value / investment - 1) * 100

# --- METRIC ---
st.subheader(f"📈 Portfolio Result for {period}")
st.metric(
    "Final Portfolio Value",
    f"${final_value:,.2f}",
    f"{growth:+.2f}%"
)

# --- PLOT (ONLY PORTFOLIO LINE) ---
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df["Date"],
    y=df["PortfolioValue"],
    mode="lines",
    name="Portfolio Value",
    line=dict(color="black", width=3)
))

fig.update_layout(
    title=f"Portfolio Value Over Time ({period})",
    xaxis_title="Date",
    yaxis_title="Value (USD)",
    template="plotly_white",
    height=500
)

st.plotly_chart(fig, use_container_width=True)

st.caption("Built by Aiman 🚀 | Data from Yahoo Finance")
