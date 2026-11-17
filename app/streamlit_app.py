"""
S&P Dow Jones Index Management & Corporate Action Control Portal
Project Codename: SPDJI-Rebalance-Net
Author: Bhupesh Chandra Dimri
"""

import streamlit as st
import pandas as pd
from src.core_engine import IndexConstituent, IndexManagementEngine

st.set_page_config(page_title="SPDJI Rebalance & Divisor Portal", layout="wide")
st.title("S&P Dow Jones Indices — Index Management & Corporate Action Divisor Engine")
st.markdown("**Real-Time Paasche Divisor Recalibration, Float-Adjusted IWF Auditing & Reconstitution Governance**")

engine = IndexManagementEngine(index_name="S&P 500 Mock Production", initial_divisor=8500000.0)
engine.add_constituent(IndexConstituent("AAPL", "Apple Inc", 185.0, 15400000.0, 0.99))
engine.add_constituent(IndexConstituent("MSFT", "Microsoft Corp", 415.0, 7450000.0, 0.98))
engine.add_constituent(IndexConstituent("NVDA", "NVIDIA Corp", 128.0, 24500000.0, 0.95))
engine.add_constituent(IndexConstituent("AMZN", "Amazon.com Inc", 178.0, 10400000.0, 0.92))
engine.add_constituent(IndexConstituent("JPM", "JPMorgan Chase & Co", 198.0, 2870000.0, 0.98))

col1, col2, col3 = st.columns(3)
col1.metric("Current Index Level", f"{engine.index_level:,.2f}")
col2.metric("Total Float Market Cap ($B)", f"${engine.total_float_market_cap / 1e9:,.2f}B")
col3.metric("Active Index Divisor", f"{engine.divisor:,.2f}")

st.subheader("Current Index Constituents & Free-Float Weighting")
df = pd.DataFrame([
    {
        "Ticker": c.ticker,
        "Name": c.name,
        "Price ($)": f"${c.price:.2f}",
        "Shares": f"{c.shares:,.0f}",
        "IWF": f"{c.iwf:.2f}",
        "Float Cap ($B)": round(c.float_market_cap / 1e9, 2),
        "Weight (%)": f"{(c.float_market_cap / engine.total_float_market_cap)*100:.2f}%"
    }
    for c in engine.constituents.values()
])
st.dataframe(df, use_container_width=True)

st.subheader("Corporate Action Divisor Simulation Sandbox")
action_type = st.selectbox("Select Corporate Event", ["Special Cash Dividend", "Stock Split (k-for-1)", "Constituent Replacement"])

if action_type == "Special Cash Dividend":
    ticker = st.selectbox("Select Constituent", list(engine.constituents.keys()))
    div_amount = st.number_input("Special Dividend per Share ($)", value=5.0, step=0.5)
    if st.button("Execute Divisor Recalibration"):
        res = engine.process_special_cash_dividend(ticker, div_amount)
        st.success(f"Recalibrated Divisor from {res['pre_divisor']:,.2f} to {res['post_divisor']:,.2f}")
        st.write(f"• Pre-Level: {res['pre_level']} | Post-Level: {res['post_level']} | Drift: {res['drift']:.2e}")
elif action_type == "Stock Split (k-for-1)":
    ticker = st.selectbox("Select Constituent for Split", list(engine.constituents.keys()))
    split_ratio = st.number_input("Split Ratio", value=2.0, step=0.5)
    if st.button("Execute Stock Split"):
        res = engine.process_stock_split(ticker, split_ratio)
        st.success(f"Stock Split processed. Divisor invariant at {res['post_divisor']:,.2f}")
        st.write(f"• Pre-Level: {res['pre_level']} | Post-Level: {res['post_level']} | Drift: {res['drift']:.2e}")
