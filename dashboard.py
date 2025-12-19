# dashboard.py
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import time
from datetime import datetime

import os
# --- CONFIGURATION ---
# Default to local, but allow Cloud URL override
BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000") 
HEADERS = {"x-api-key": os.getenv("MOBILE_API_KEY", "secret_mobile_key_123")}

st.set_page_config(page_title="QuantAI Pro Terminal", page_icon="🏦", layout="wide", initial_sidebar_state="expanded")

# --- STYLES ---
st.markdown("""
    <style>
    .stMetric {
        background-color: #0E1117;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #303030;
    }
    .big-font { font-size: 20px !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: STATUS & MANUAL ---
st.sidebar.title("⚡ QuantAI Terminal")
st.sidebar.caption("v2.0 Professional Edition")

# System Check
try:
    requests.get(f"{BASE_URL}/")
    st.sidebar.success("🟢 System Online")
except:
    st.sidebar.error("🔴 System Offline")

st.sidebar.divider()

# --- PENDING APPROVALS ---
try:
    pending_resp = requests.get(f"{BASE_URL}/trade/pending", headers=HEADERS)
    if pending_resp.status_code == 200:
        pending_orders = pending_resp.json()
        if pending_orders:
            st.sidebar.error(f"🔔 {len(pending_orders)} Approval(s) Pending")
            for order in pending_orders:
                with st.sidebar.expander(f"Wait: {order['symbol']} ({order['action']})", expanded=True):
                    st.write(f"**Qty:** {order['quantity']} @ ₹{order['price']}")
                    st.caption(f"Reason: AI Signal")
                    
                    c1, c2 = st.columns(2)
                    if c1.button("✅", key=f"app_{order['id']}", help="Approve"):
                        res = requests.post(f"{BASE_URL}/trade/approve/{order['id']}", headers=HEADERS)
                        if res.status_code == 200: st.success("Approved!")
                        st.experimental_rerun()
                        
                    if c2.button("❌", key=f"rej_{order['id']}", help="Reject"):
                         requests.post(f"{BASE_URL}/trade/reject/{order['id']}", headers=HEADERS)
                         st.warning("Rejected.")
                         st.experimental_rerun()
except Exception as e:
    # st.sidebar.error(f"Connection Error: {e}")
    pass

st.sidebar.divider()

# Manual Trading
with st.sidebar.expander("🛒 Manual Execution", expanded=True):
    man_symbol = st.text_input("Symbol", value="RELIANCE").upper()
    c1, c2 = st.columns(2)
    man_action = c1.radio("Side", ["BUY", "SELL"], label_visibility="collapsed")
    man_qty = c2.number_input("Qty", min_value=1, value=10)
    
    if st.button("🚀 Execute Order", type="primary", use_container_width=True):
        try:
             # Fetch Live Price
             sym = man_symbol if man_symbol.endswith(".NS") else f"{man_symbol}.NS"
             ticker = yf.Ticker(sym)
             hist = ticker.history(period='1d')
             curr_price = hist['Close'].iloc[-1]
             
             resp = requests.post(f"{BASE_URL}/trade/{sym}?action={man_action}&qty={man_qty}&price={curr_price}", headers=HEADERS)
             if resp.status_code == 200:
                 st.success("Order Placed!")
             else:
                 st.error(f"Failed: {resp.text}")
        except Exception as e:
            st.error(f"Error: {e}")

st.sidebar.divider()
selected_sector = st.sidebar.selectbox("🔎 Scanner Sector", ["All", "Bank", "IT", "Auto", "Pharma", "FMCG", "Metal"])

# --- HEADER STATISTICS ---
try:
    bal_resp = requests.get(f"{BASE_URL}/balance", headers=HEADERS)
    if bal_resp.status_code == 200:
        bal = bal_resp.json()
        roi = ((bal['total_equity'] - bal['initial_balance']) / bal['initial_balance']) * 100
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Equity", f"₹{bal['total_equity']:,.0f}", f"{roi:.2f}%")
        c2.metric("Cash", f"₹{bal['current_cash']:,.0f}")
        c3.metric("Portfolio", f"₹{bal['portfolio_value']:,.0f}")
        c4.metric("Day P&L", "₹0.00", "0.00%") # Placeholder for now
except:
    st.error("Connecting to server...")

# --- TABS ---
t1, t2, t3 = st.tabs(["🚀 Opportunities (Scanner)", "🔬 Market Lab", "📜 Orders & Positions"])

# --- TAB 1: SCANNER ---
with t1:
    col_scan_btn, col_last_scan = st.columns([1, 4])
    if col_scan_btn.button("Run Full Scan", type="primary"):
        with st.spinner(f"AI Scanning {selected_sector}..."):
             resp = requests.get(f"{BASE_URL}/scan?sector={selected_sector}", headers=HEADERS)
             if resp.status_code == 200:
                 st.session_state['scan_data'] = resp.json()
    
    if 'scan_data' in st.session_state:
        data = st.session_state['scan_data']
        best = data.get("best_pick")
        
        if best:
            st.markdown("### 🏆 Top AI Pick")
            
            # Top Pick Card
            with st.container():
                c1, c2, c3 = st.columns([1, 2, 1])
                c1.markdown(f"## {best['symbol']}")
                c1.caption(best['trade_type'])
                c1.metric("Signal Price", f"₹{best['price']}")
                
                c2.markdown(f"**Reasons:** {best['reasons']}")
                if 'reasoning_list' in best:
                     for r in best['reasoning_list']:
                         c2.caption(f"• {r}")
                
                c2.markdown(f"**Market:** {best['patterns']}")
                
                # Targets
                if 'conservative_target' in best:
                    c2.info(f"Targets: ₹{best['conservative_target']} (Safe) | ₹{best['aggressive_target']} (Max)")
                    c2.caption(f"SL: ₹{best['stop_loss']}")
                else:
                    c2.info(f"Target: {best.get('target',0)} | SL: {best.get('stop_loss',0)}")
                
                c3.metric("Confidence", f"{best['score']}%")
                if c3.button(f"Buy {best['symbol']}", key="buy_best"):
                     requests.post(f"{BASE_URL}/trade/{best['symbol']}?action=BUY&qty=10&price={best['price']}&stop_loss={best.get('stop_loss')}&target={best.get('target')}", headers=HEADERS)
                     st.success("Trade Executed!")
            
            # Cost Analysis Section
            if 'cost_breakdown' in best:
                costs = best['cost_breakdown']
                with st.expander(f"💸 Brokerage & Taxes (For 10 Qty @ ₹{best['price']})", expanded=False):
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Brokerage", f"₹{costs['brokerage']}")
                    c2.metric("STT & Charges", f"₹{round(costs['stt'] + costs['total_charges'] - costs['brokerage'] - costs['stt'], 2)}")
                    c3.metric("Total Tax", f"₹{costs['total_charges']}")
                    c4.metric("Break-Even", f"₹{costs['net_price']}")
                    st.caption(f"Net Price needed to cover ₹{costs['total_charges']} in taxes.")
        else:
            st.warning("No High Confidence Setups Found.")

        st.divider()
        st.markdown("### 📋 Market Watchlist")
        if data.get('market_data'):
            df = pd.DataFrame(data['market_data'])
            st.dataframe(df, use_container_width=True)

# --- TAB 2: MARKET LAB ---
with t2:
    st.subheader("Deep Dive Analysis")
    sym_in = st.text_input("Analyze Symbol", "INFY").upper()
    
    if st.button("Analyze"):
        with st.spinner("Crunching Numbers..."):
            sym = sym_in if sym_in.endswith(".NS") else f"{sym_in}.NS"
            resp = requests.get(f"{BASE_URL}/analyze/{sym}", headers=HEADERS)
            if resp.status_code == 200:
                report = resp.json()
                
                # Layout
                c1, c2, c3 = st.columns(3)
                c1.metric("Trend", report['trend'])
                c2.metric("AI Verdict", report['ai_verdict'])
                c3.metric("Risk:Reward", report['risk_reward'])
                
                st.write(f"**Condition:** {report.get('market_condition','N/A')}")
                
                # AI Reasoning
                if 'reasoning_list' in report:
                    st.markdown("#### 🧠 AI Reasoning")
                    for r in report['reasoning_list']:
                        st.markdown(f"- {r}")
                
                # Targets Section
                st.markdown("#### 🎯 Targets & Exits")
                tc1, tc2, tc3 = st.columns(3)
                tc1.metric("Stop Loss", f"₹{report.get('stop_loss',0)}")
                
                if 'conservative_target' in report:
                    tc2.metric("Safe Exit", f"₹{report['conservative_target']}")
                    tc3.metric("Aggressive Exit", f"₹{report['aggressive_target']}")
                else:
                    tc2.metric("Target", f"₹{report.get('target',0)}")

                # Cost Analysis
                if 'cost_breakdown' in report:
                    costs = report['cost_breakdown']
                    with st.expander(f"💸 Brokerage Calculator (10 Qty)", expanded=False):
                        mc1, mc2, mc3 = st.columns(3)
                        mc1.write(f"**Turnover:** ₹{costs['turnover']}")
                        mc1.write(f"**Brokerage:** ₹{costs['brokerage']}")
                        mc2.write(f"**STT:** ₹{costs['stt']}")
                        mc2.write(f"**Total Tax:** ₹{costs['total_charges']}")
                        mc3.write(f"**Net Buy Price:** ₹{costs['net_price']}")
                        mc3.caption("Price to exit at no loss")
                
                # Chart
                chart_df = yf.download(sym, period="6mo", progress=False)
                # Fix MultiIndex if present
                if isinstance(chart_df.columns, pd.MultiIndex):
                     chart_df.columns = chart_df.columns.get_level_values(0)

                if not chart_df.empty:
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(x=chart_df.index,
                                    open=chart_df['Open'], high=chart_df['High'],
                                    low=chart_df['Low'], close=chart_df['Close'], name='Price'))
                    
                    # Add Indicators if possible (need to calc manually here or trust report)
                    # Simple MA for visual
                    ma50 = chart_df['Close'].rolling(50).mean()
                    fig.add_trace(go.Scatter(x=chart_df.index, y=ma50, line=dict(color='orange', width=1), name='50 MA'))
                    
                    # Levels
                    if report.get('conservative_target'):
                        fig.add_hline(y=report['conservative_target'], line_dash="dash", line_color="green", annotation_text="Safe Tgt")
                    if report.get('aggressive_target'):
                        fig.add_hline(y=report['aggressive_target'], line_dash="dot", line_color="cyan", annotation_text="Max Tgt")
                    if report.get('stop_loss'):
                        fig.add_hline(y=report['stop_loss'], line_dash="dash", line_color="red", annotation_text="SL")

                    fig.update_layout(template="plotly_dark", height=500, xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)

# --- TAB 3: TRADES ---
with t3:
    st.subheader("Order Book")
    try:
        ledger = requests.get(f"{BASE_URL}/ledger", headers=HEADERS).json()
        if ledger:
            st.dataframe(pd.DataFrame(ledger).iloc[::-1], use_container_width=True)
        else:
            st.info("No trades yet.")
    except: # Fixed indentation
        st.error("Error fetching ledger") # Fixed indentation
