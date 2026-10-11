import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ==========================================
# KALLY07 FX VISIONARIES AI SCANNER
# ==========================================

st.set_page_config(
    page_title="KALLY07 FX VISIONARIES",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #080b12;
    color: #f5f5f5;
}
h1, h2, h3 {
    color: #d4af37 !important;
}
[data-testid="stMetric"] {
    background-color: #141a26;
    border: 1px solid #d4af37;
    padding: 12px;
    border-radius: 10px;
}
.stButton > button {
    background-color: #d4af37;
    color: #080b12;
    font-weight: bold;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

st.title("👑 KALLY07 FX VISIONARIES")
st.caption("AI-ASSISTED FOREX & GOLD MARKET SCANNER")

st.warning(
    "Research prototype: signals are estimates, not financial advice. "
    "Market data may be delayed or unavailable. Test before trading."
)

# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("⚙️ Scanner Settings")

market = st.sidebar.selectbox(
    "Select Market",
    [
        "Gold (XAU/USD)",
        "EUR/USD",
        "GBP/USD",
        "USD/JPY",
        "AUD/USD",
        "USD/CAD",
        "NZD/USD",
        "EUR/GBP"
    ]
)

timeframe = st.sidebar.selectbox(
    "Analysis Timeframe",
    ["5 minutes (M5)", "15 minutes (M15)"]
)

symbol_map = {
    "Gold (XAU/USD)": "XAUUSD=X",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "CAD=X",
    "NZD/USD": "NZDUSD=X",
    "EUR/GBP": "EURGBP=X"
}

symbol = symbol_map[market]
interval = "5m" if "M5" in timeframe else "15m"

if st.sidebar.button("🔄 Refresh Analysis"):
    st.cache_data.clear()

# ==========================================
# MARKET DATA
# ==========================================

@st.cache_data(ttl=60)
def load_data(ticker, interval_value):
    data = yf.download(
        ticker,
        period="5d",
        interval=interval_value,
        auto_adjust=False,
        progress=False
    )

    if data.empty:
        return pd.DataFrame()

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    required = ["Open", "High", "Low", "Close"]
    data = data.dropna(subset=required)

    return data


with st.spinner("Loading market data..."):
    try:
        df = load_data(symbol, interval)
    except Exception:
        df = pd.DataFrame()

if df.empty or len(df) < 30:
    st.error(
        "Market data is unavailable or insufficient. "
        "Try again later. This data source may not provide every symbol "
        "or timeframe consistently."
    )
    st.stop()

# ==========================================
# INDICATORS
# ==========================================

df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

previous_close = df["Close"].shift(1)

true_range = pd.concat(
    [
        df["High"] - df["Low"],
        (df["High"] - previous_close).abs(),
        (df["Low"] - previous_close).abs()
    ],
    axis=1
).max(axis=1)

df["ATR"] = true_range.rolling(14).mean()

latest = df.iloc[-1]
price = float(latest["Close"])
ema20 = float(latest["EMA20"])
ema50 = float(latest["EMA50"])
atr = float(latest["ATR"])

if not np.isfinite(atr) or atr <= 0:
    atr = float((df["High"] - df["Low"]).tail(14).mean())

# ==========================================
# BASIC MARKET STRUCTURE
# ==========================================

recent = df.tail(20)

swing_high = float(recent["High"].iloc[:-1].max())
swing_low = float(recent["Low"].iloc[:-1].min())

bullish_structure = price > swing_high
bearish_structure = price < swing_low

# Simple three-candle Fair Value Gap heuristic
bullish_fvg = False
bearish_fvg = False

if len(df) >= 3:
    candle_1 = df.iloc[-3]
    candle_3 = df.iloc[-1]

    bullish_fvg = float(candle_3["Low"]) > float(candle_1["High"])
    bearish_fvg = float(candle_3["High"]) < float(candle_1["Low"])

# ==========================================
# SIGNAL LOGIC
# ==========================================

trend_bullish = price > ema20 > ema50
trend_bearish = price < ema20 < ema50

signal = "WAIT"
reason = "The preliminary conditions do not align."

if trend_bullish and bullish_structure and bullish_fvg:
    signal = "BUY"
    reason = (
        "Bullish EMA alignment, a recent high break, "
        "and a possible bullish three-candle gap."
    )

elif trend_bearish and bearish_structure and bearish_fvg:
    signal = "SELL"
    reason = (
        "Bearish EMA alignment, a recent low break, "
        "and a possible bearish three-candle gap."
    )

# ==========================================
# ENTRY, STOP LOSS & TAKE PROFIT ESTIMATES
# ==========================================

if signal == "BUY":
    entry = price
    stop_loss = entry - (1.5 * atr)
    take_profit = entry + (3.0 * atr)

elif signal == "SELL":
    entry = price
    stop_loss = entry + (1.5 * atr)
    take_profit = entry - (3.0 * atr)

else:
    entry = price
    stop_loss = None
    take_profit = None

# ==========================================
# DASHBOARD
# ==========================================

st.subheader(f"📈 {market} — {timeframe}")

col1, col2, col3 = st.columns(3)

col1.metric("Latest Data Price", f"{price:.5f}")
col2.metric("EMA 20", f"{ema20:.5f}")
col3.metric("EMA 50", f"{ema50:.5f}")

st.caption(
    f"Data timestamp: {df.index[-1]} | "
    "Source: Yahoo Finance, not a direct XM feed"
)

st.divider()

st.subheader("🎯 Preliminary Signal")

if signal == "BUY":
    st.success("🟢 BUY CONDITIONS DETECTED")
elif signal == "SELL":
    st.error("🔴 SELL CONDITIONS DETECTED")
else:
    st.info("⏳ WAIT — NO QUALIFIED SIGNAL")

st.write(reason)

if signal in ["BUY", "SELL"]:
    c1, c2, c3 = st.columns(3)

    c1.metric("Estimated Entry", f"{entry:.5f}")
    c2.metric("Estimated Stop Loss", f"{stop_loss:.5f}")
    c3.metric("Estimated Take Profit", f"{take_profit:.5f}")

    st.caption(
        "These levels use a simple ATR calculation. "
        "They are not validated trading recommendations."
    )
else:
    st.metric("Reference Price", f"{price:.5f}")
    st.write("No entry, Stop Loss, or Take Profit is recommended by this prototype.")

st.divider()

# ==========================================
# CANDLESTICK CHART
# ==========================================

st.subheader("🕯️ Price Chart")

chart_data = df.tail(100)

fig = go.Figure()

fig.add_trace(
    go.Candlestick(
        x=chart_data.index,
        open=chart_data["Open"],
        high=chart_data["High"],
        low=chart_data["Low"],
        close=chart_data["Close"],
        name="Price"
    )
)

fig.add_trace(
    go.Scatter(
        x=chart_data.index,
        y=chart_data["EMA20"],
        name="EMA 20",
        line=dict(width=1)
    )
)

fig.add_trace(
    go.Scatter(
        x=chart_data.index,
        y=chart_data["EMA50"],
        name="EMA 50",
        line=dict(width=1)
    )
)

fig.update_layout(
    template="plotly_dark",
    paper_bgcolor="#080b12",
    plot_bgcolor="#080b12",
    xaxis_rangeslider_visible=False,
    height=450,
    margin=dict(l=5, r=5, t=30, b=5)
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================
# SMC-STYLE OBSERVATIONS
# ==========================================

st.subheader("🧠 Market Structure Observations")

a, b = st.columns(2)

a.metric(
    "Recent Swing High",
    f"{swing_high:.5f}"
)

b.metric(
    "Recent Swing Low",
    f"{swing_low:.5f}"
)

if bullish_structure:
    st.write("Possible bullish break above the recent 20-candle high.")
elif bearish_structure:
    st.write("Possible bearish break below the recent 20-candle low.")
else:
    st.write("No break of the recent 20-candle range detected.")

if bullish_fvg:
    st.write("Possible bullish three-candle Fair Value Gap detected.")
elif bearish_fvg:
    st.write("Possible bearish three-candle Fair Value Gap detected.")
else:
    st.write("No three-candle Fair Value Gap detected by this simple rule.")

st.divider()

# ==========================================
# ECONOMIC NEWS STATUS
# ==========================================

st.subheader("📰 Fundamental News")

st.warning(
    "Live economic calendar is not connected yet. "
    "This version does not verify high-impact news or determine "
    "fundamental BUY/SELL bias. Check an economic calendar before "
    "considering any trade."
)

# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "KALLY07 FX VISIONARIES AI SCANNER | Prototype version 1.0"
)

st.caption(
    f"Dashboard refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

st.caption(
    "Educational tool only. Signals can be wrong. "
    "No automated trading or XM account connection is implemented."
)
