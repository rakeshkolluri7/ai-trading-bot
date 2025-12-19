# src/scanner.py
import joblib
import os
import pandas as pd
import ta
import numpy as np
from src.data_loader import fetch_data
from src.news_analyzer import NewsAnalyzer
from src.indicators import check_candlestick_patterns, add_indicators
from src.config import MODEL_PATH
from src.sectors import get_stocks_by_sector
from src.calculator import calculate_delivery_costs
from src.market_analyzer import get_market_condition
from src.indicators import check_candlestick_patterns, add_indicators, check_breakout

def get_ai_prediction(symbol, df):
    try:
        clean_symbol = symbol.replace('.NS', '')
        model_file = f"{MODEL_PATH}/{clean_symbol}_model.pkl"
        
        if not os.path.exists(model_file): return 0
        model = joblib.load(model_file)
        
        # Calculate indicators exactly how we trained them
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
        
        features = ['RSI', 'SMA_20', 'SMA_50', 'Close', 'Volume']
        last_row = df[features].iloc[[-1]]
        
        # Convert numpy int64 to python int
        return int(model.predict(last_row)[0])
    except Exception:
        return 0

def analyze_single_stock(symbol):
    """
    Performs a deep-dive analysis on a single stock using Professional Indicators.
    """
    print(f"🔬 Deep Analyzing {symbol}...")
    news_bot = NewsAnalyzer()
    
    try:
        # Get 1 Year Data
        df = fetch_data(symbol, period="1y")
        if df.empty: return {"error": "No Data Found"}

        df = add_indicators(df)
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # --- 1. MARKET & TREND CONTEXT ---
        market_cond = get_market_condition(df)
        supertrend_signal = "BUY" if curr['SuperTrend_Signal'] else "SELL"
        
        trend = "SIDEWAYS"
        if "TRENDING UP" in market_cond: trend = "STRONG UPTREND 🚀"
        elif "TRENDING DOWN" in market_cond: trend = "STRONG DOWNTREND 🔻"
        elif curr['Close'] > curr['EMA_Slow']: trend = "MILD UPTREND ↗️"
        elif curr['Close'] < curr['EMA_Slow']: trend = "MILD DOWNTREND ↘️"
        
        # --- 2. MULTI-INDICATOR CONFIRMATION ---
        signals = []
        
        # A. Trend Verification
        if curr['Close'] > curr['SuperTrend']: signals.append("SuperTrend Bullish")
        if curr['ADX'] > 25: signals.append("Strong Momentum (ADX>25)")
        
        # B. Momentum
        if curr['RSI'] > 50 and curr['RSI'] > prev['RSI']: signals.append("RSI Rising")
        if curr['MACD'] > 0 and curr['MACD'] > prev['MACD']: signals.append("MACD Bullish")
        
        # C. Volume/Price Action
        if curr['Close'] > curr['VWAP']: signals.append("Price > VWAP (Inst. Support)")
        if curr['OBV'] > df['OBV'].iloc[-5]: signals.append("OBV Rising")
        
        # Count Confirmations
        conf_score = len(signals)
        
        # --- 3. RISK & ENTRY ---
        atr = curr['ATR']
        stop_loss = round(curr['Close'] - (1.5 * atr), 2) # Tighter SL for intraday
        target = round(curr['Close'] + (3 * atr), 2)      # 1:2 Risk Reward
        risk = curr['Close'] - stop_loss
        reward = target - curr['Close']
        rr_ratio = round(reward / risk, 1) if risk > 0 else 0
        
        risk_reward = f"1:{rr_ratio} (Risk ₹{round(risk, 1)})"
        
        # --- 4. STRATEGY CLASSIFICATION ---
        trade_type = "NO TRADE"
        ai_verdict = "WAIT"
        
        if conf_score >= 4 and "UPTREND" in trend:
            trade_type = "MOMENTUM BUY"
            ai_verdict = "BUY"
        elif conf_score >= 3 and curr['RSI'] < 40 and "UPTREND" in trend:
            trade_type = "PULLBACK BUY"
            ai_verdict = "BUY"
        elif curr['Close'] > df['High'].iloc[-20:].max():
             trade_type = "BREAKOUT BUY"
             ai_verdict = "BUY"
            
        # --- 5. AI & SENTIMENT ---
        sent_score, _ = news_bot.get_sentiment(symbol)
        sentiment_text = "Neutral"
        if sent_score > 0.2: sentiment_text = "Positive 🟢"
        if sent_score < -0.2: sentiment_text = "Negative 🔴"

        decision = "GOOD" if ai_verdict == "BUY" and rr_ratio >= 2.0 else "AVOID"
        
        # --- 6. TARGETS & EXITS ---
        # Conservative: 1.5x ATR or Recent Structure
        cons_target = round(curr['Close'] + (1.5 * atr), 2)
        # Aggressive: 3.0x ATR
        agg_target = round(curr['Close'] + (3.0 * atr), 2)
        
        # --- 7. COST ANALYSIS ---
        costs = calculate_delivery_costs(float(curr['Close']), 10)

        # --- CONSTRUCT REPORT ---
        return {
            "symbol": symbol,
            "current_price": round(float(curr['Close']), 2),
            "trend": trend,
            "market_condition": market_cond,
            "volume_strength": "High" if curr['Volume'] > df['Volume'].mean() else "Normal",
            "ai_verdict": ai_verdict,
            "trade_type": trade_type,
            "sentiment": sentiment_text,
            "conf_score": f"{conf_score}/6 Indicators",
            "signals": ", ".join(signals),
            "stop_loss": stop_loss,
            "target": target, # Legacy single target
            "conservative_target": cons_target,
            "aggressive_target": agg_target,
            "risk_reward": risk_reward,
            "decision": decision,
            "reason": f"Signals: {len(signals)} confirmed. {market_cond}. RR: {rr_ratio}",
            "reasoning_list": signals, # List for UI bullet points
            "cost_breakdown": costs,
            "total_tax": float(costs['total_charges']),
            "break_even": float(costs['net_price'])
        }

    except Exception as e:
        return {"error": str(e)}

def scan_market(sector="All"):
    print(f"[INFO] Senior Quant Analyzing Sector: {sector}...")
    news_bot = NewsAnalyzer()
    
    stock_list = get_stocks_by_sector(sector)
    report = []

    for symbol in stock_list:
        try:
            df = fetch_data(symbol, period="1y")
            if df.empty: continue

            df = add_indicators(df)
            current = df.iloc[-1]
            
            # Use same logic as single stock analysis
            market_cond = get_market_condition(df)
            
            # Quick Signal Check
            score = 0
            reasons = []
            
            # 1. SuperTrend (Major Filter)
            if current['SuperTrend_Signal']: 
                score += 20
                reasons.append("SuperTrend Buy")
            
            # 2. VWAP
            if current['Close'] > current['VWAP']:
                score += 15
                reasons.append("> VWAP")
                
            # 3. RSI Momentum
            if 50 < current['RSI'] < 70:
                score += 10
            elif current['RSI'] > 70:
                score += 5 
                reasons.append("Strong Momtum")
                
            # 4. ADX Trend Strength
            if current['ADX'] > 25:
                score += 15
                reasons.append("Strong Trend")
                
            # 5. Breakout
            breakout = check_breakout(df)
            if breakout and "Bullish" in breakout:
                score += 25
                reasons.append("Breakout Detected")
            
            # 6. AI Model Prediction (Existing)
            ai_sig = get_ai_prediction(symbol, df)
            if ai_sig == 1:
                score += 15
                reasons.append("AI Model")

            confidence = min(100, score)
            
            if score >= 60: # Threshold for showing in scanner
                costs = calculate_delivery_costs(float(current['Close']), 10)
                
                # Risk Calc for Scanner
                atr = current['ATR']
                stop_loss = round(current['Close'] - (1.5 * atr), 2)
                target = round(current['Close'] + (3 * atr), 2)
                
                entry = {
                    "symbol": str(symbol),
                    "price": round(float(current['Close']), 2),
                    "score": int(confidence),
                    "ai_says": "BUY",
                    "reasons": " + ".join(reasons),
                    "trade_type": "Momentum" if current['ADX'] > 25 else "Swing",
                    "stop_loss": stop_loss,
                    "target": target,
                    "risk_reward": "1:2",
                    "break_even": float(costs['net_price']),
                    "total_tax": float(costs['total_charges']),
                    "cost_breakdown": costs,
                    "patterns": market_cond, 
                    "indicators": f"ADX:{int(current['ADX'])} RSI:{int(current['RSI'])} ST:{'Green' if current['SuperTrend_Signal'] else 'Red'}"
                }
                report.append(entry)
                print(f"   🔎 {symbol}: Score {confidence}%")

        except Exception as e:
            # print(f"   ❌ Error {symbol}: {e}")
            pass

    if report:
        report = sorted(report, key=lambda x: x['score'], reverse=True)
        return report[0], report
    return None, []