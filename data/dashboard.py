# dashboard.py
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf
import time

# --- CONFIGURATION ---
BASE_URL = "http://127.0.0.1:8000" 
HEADERS = {"x-api-key": "secret_mobile_key_123"}

st.set_page_config(page_title="Pro Quant AI Dashboard", page_icon="📈", layout="wide")

# --- SIDEBAR: MANUAL TRADING ---
st.sidebar.title("⚡ Control Panel")

# 1. System Status
try:
    requests.get(f"{BASE_URL}/")
    st.sidebar.success("🟢 System Online")
except:
    st.sidebar.error("🔴 System Offline")

# 2. Manual Trade Widget
st.sidebar.divider()
st.sidebar.subheader("🛒 Instant Order")
man_symbol = st.sidebar.text_input("Symbol", value="TCS").upper()
man_action = st.sidebar.radio("Action", ["BUY", "SELL"], horizontal=True)
man_qty = st.sidebar.number_input("Qty", min_value=1, value=1)

if st.sidebar.button("🚀 Execute Order", type="primary"):
    with st.spinner("Processing..."):
        try:
            # 1. Get Live Price First
            sym = man_symbol if man_symbol.endswith(".NS") else f"{man_symbol}.NS"
            ticker = yf.Ticker(sym)
            history = ticker.history(period="1d")
            
            if not history.empty:
                current_price = history['Close'].iloc[-1]
                
                # 2. Send Order to Server
                trade_url = f"{BASE_URL}/trade/{sym}?action={man_action}&qty={man_qty}&price={current_price}"
                resp = requests.post(trade_url, headers=HEADERS)
                
                if resp.status_code == 200:
                    st.sidebar.success(f"✅ {man_action} {man_qty} {sym} @ {current_price:.2f}")
                    # Store success in session state to show on main page
                    st.session_state['last_order'] = {
                        "symbol": sym,
                        "action": man_action,
                        "qty": man_qty,
                        "price": current_price,
                        "status": "Success"
                    }
                    time.sleep(1)
                    st.rerun() # Refresh to show new balance
                else:
                    st.sidebar.error(f"❌ Failed: {resp.text}")
            else:
                st.sidebar.error("❌ Invalid Symbol or No Data")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

# 3. Sector Selector (For Scanner)
st.sidebar.divider()
st.sidebar.subheader("📡 Scanner Config")
try:
    sec_resp = requests.get(f"{BASE_URL}/sectors")
    sectors = ["All"] + sec_resp.json().get("sectors", []) if sec_resp.status_code == 200 else ["All"]
    selected_sector = st.sidebar.selectbox("Select Sector:", sectors)
except:
    selected_sector = "All"

# --- MAIN DASHBOARD ---
st.title("📈 Pro Quant AI Dashboard")

# --- ORDER CONFIRMATION BANNER ---
if 'last_order' in st.session_state:
    order = st.session_state['last_order']
    st.info(f"🔔 **Last Order Executed:** {order['action']} {order['qty']} {order['symbol']} at ₹{order['price']:.2f}")
    if st.button("Clear Notification"):
        del st.session_state['last_order']
        st.rerun()

# --- ACCOUNT SCORECARD ---
try:
    bal_resp = requests.get(f"{BASE_URL}/balance", headers=HEADERS)
    if bal_resp.status_code == 200:
        bal = bal_resp.json()
        roi = ((bal['total_equity'] - bal['initial_balance']) / bal['initial_balance']) * 100
        
        b1, b2, b3 = st.columns(3)
        b1.metric("💰 Cash Available", f"₹{bal['current_cash']:,.2f}")
        b2.metric("💼 Portfolio Value", f"₹{bal['portfolio_value']:,.2f}")
        b3.metric("📈 Total Equity", f"₹{bal['total_equity']:,.2f}", f"{roi:.2f}%")
        st.divider()
except:
    st.error("Could not fetch account balance. Is server running?")

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Market Scanner", "🔬 Deep Analysis", "📜 Portfolio & Ledger", "🧠 AI Brain"])

# --- TAB 1: SCANNER ---
with tab1:
    if st.button(f"Scan {selected_sector} Sector"):
        with st.spinner(f"Scanning {selected_sector}..."):
            try:
                resp = requests.get(f"{BASE_URL}/scan?sector={selected_sector}", headers=HEADERS, timeout=120)
                if resp.status_code == 200:
                    data = resp.json()
                    best = data.get("best_pick")
                    if best:
                        st.success(f"🏆 TOP PICK: {best['symbol']}")
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Price", f"₹{best['price']}")
                        c2.metric("Score", f"{best['score']}%")
                        c3.metric("AI Verdict", best['ai_says'])
                        
                        # --- CALCULATION DISPLAY ---
                        break_even = best.get('break_even', 0)
                        total_tax = best.get('total_tax', 0)
                        c4.metric("Break-Even", f"₹{break_even}")
                        
                        st.info(f"💡 {best.get('reasons')}")
                        st.caption(f"📊 Tech: {best.get('indicators')}")
                        
                        # Cost Breakdown Expander
                        with st.expander("💰 Detailed Cost Breakdown (For 10 Qty)"):
                            st.write(f"**Buy Price:** ₹{best['price']}")
                            st.write(f"**Total Taxes & Charges:** ₹{total_tax}")
                            st.write(f"**Net Break-Even Price:** ₹{break_even}")
                            st.caption("*Includes Brokerage, STT, Exchange Fees, SEBI, GST, Stamp Duty")

                        # Quick Buy from Scanner
                        if st.button(f"Buy {best['symbol']} Now"):
                            requests.post(f"{BASE_URL}/trade/{best['symbol']}?action=BUY&qty=10&price={best['price']}", headers=HEADERS)
                            st.success("Order Placed!")
                            st.session_state['last_order'] = {
                                "symbol": best['symbol'],
                                "action": "BUY",
                                "qty": 10,
                                "price": best['price'],
                                "status": "Success"
                            }
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.warning("No high-confidence setups found.")
                else:
                    st.error(f"Scan failed: {resp.text}")
            except Exception as e:
                st.error(f"Error: {e}")

# --- TAB 2: DEEP ANALYSIS ---
with tab2:
    st.header("Stock Deep Dive")
    col_sym, col_btn = st.columns([3, 1])
    symbol_input = col_sym.text_input("Enter Symbol (e.g., RELIANCE):").upper()
    if col_btn.button("Analyze"):
        if symbol_input:
            with st.spinner("Analyzing..."):
                try:
                    sym = symbol_input if symbol_input.endswith(".NS") else f"{symbol_input}.NS"
                    resp = requests.get(f"{BASE_URL}/analyze/{sym}", headers=HEADERS)
                    if resp.status_code == 200:
                        data = resp.json()
                        if "error" in data:
                            st.error(data['error'])
                        else:
                            # Metrics
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Verdict", data['decision'])
                            m2.metric("Trend", data['trend'])
                            m3.metric("AI", data['ai_verdict'])
                            
                            # Chart
                            st.write("### 🕯️ Chart")
                            chart_df = yf.download(sym, period="1y", progress=False)
                            # Fix MultiIndex
                            if isinstance(chart_df.columns, pd.MultiIndex):
                                chart_df.columns = chart_df.columns.get_level_values(0)
                                
                            if not chart_df.empty:
                                fig = go.Figure()
                                fig.add_trace(go.Candlestick(x=chart_df.index, open=chart_df['Open'], high=chart_df['High'], low=chart_df['Low'], close=chart_df['Close'], name='Price'))
                                sma50 = chart_df['Close'].rolling(window=50).mean()
                                fig.add_trace(go.Scatter(x=chart_df.index, y=sma50, line=dict(color='orange'), name='50 SMA'))
                                fig.update_layout(xaxis_rangeslider_visible=False, height=350, margin=dict(l=0, r=0, t=0, b=0))
                                st.plotly_chart(fig, use_container_width=True) # Fixed parameter
                            
                            # Cost Analysis for Single Stock
                            total_tax = data.get('total_tax', 0)
                            break_even = data.get('break_even', 0)
                            
                            st.write(f"**Strategy:** {data['strategy']}")
                            st.write(f"**Reason:** {data['reason']}")
                            
                            st.info("💰 **Cost Analysis (10 Qty)**")
                            c_a, c_b = st.columns(2)
                            c_a.metric("Total Taxes", f"₹{total_tax}")
                            c_b.metric("Break-Even", f"₹{break_even}")

                            st.info(f"🎯 Target: ₹{data['target']} | 🛑 Stop Loss: ₹{data['stop_loss']}")
                            
                except Exception as e:
                    st.error(f"Error: {e}")

# --- TAB 3: PORTFOLIO & LEDGER ---
with tab3:
    col_p1, col_p2 = st.columns([2, 1])
    
    with col_p1:
        st.subheader("📜 Recent Trades")
        try:
            resp = requests.get(f"{BASE_URL}/ledger", headers=HEADERS)
            if resp.status_code == 200:
                trades = resp.json()
                if trades:
                    # Show latest trades first
                    df = pd.DataFrame(trades).iloc[::-1]
                    # Fixed parameter: replaced use_container_width with use_container_width=True
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No trades yet.")
        except:
            st.error("Connection failed.")

    with col_p2:
        st.subheader("💼 Position Manager")
        # Logic to calculate holdings would go here (requires parsing ledger)
        # For now, simple manual sell helper
        st.info("To sell a position, use the Sidebar 'Instant Order' panel.")
        
        if st.button("🔄 Refresh Ledger"):
            st.rerun()

# --- TAB 4: AI BRAIN ---
with tab4:
    st.info("AI Model details coming soon.")