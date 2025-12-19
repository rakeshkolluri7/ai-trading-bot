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
    Performs a deep-dive analysis on a single stock.
    Returns a detailed dictionary with Trend, Structure, Volume, and Plan.
    """
    print(f"🔬 Deep Analyzing {symbol}...")
    news_bot = NewsAnalyzer()
    
    try:
        # Get 1 Year Data
        df = fetch_data(symbol, period="1y")
        if df.empty: return {"error": "No Data Found"}

        df = add_indicators(df)
        curr = df.iloc[-1]
        
        # --- 1. TREND & STRUCTURE ---
        sma_50 = ta.trend.sma_indicator(df['Close'], window=50).iloc[-1]
        sma_200 = ta.trend.sma_indicator(df['Close'], window=200).iloc[-1]
        
        trend = "SIDEWAYS"
        if curr['Close'] > sma_50 > sma_200: trend = "STRONG UPTREND 🚀"
        elif curr['Close'] < sma_50 < sma_200: trend = "STRONG DOWNTREND 🔻"
        elif curr['Close'] > sma_50: trend = "WEAK UPTREND ↗️"
        elif curr['Close'] < sma_50: trend = "WEAK DOWNTREND ↘️"
        
        # --- 2. VOLUME CONFIRMATION ---
        vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
        vol_strength = "Low"
        if curr['Volume'] > vol_avg * 2: vol_strength = "Ultra High (Institutions?)"
        elif curr['Volume'] > vol_avg * 1.2: vol_strength = "High"
        
        # --- 3. RISK & ENTRY ---
        atr = curr['ATR']
        stop_loss = round(curr['Close'] - (2 * atr), 2)
        target = round(curr['Close'] + (4 * atr), 2)
        risk_reward = f"1:2 (Risk ₹{round(2*atr, 1)})"
        
        # --- 4. STRATEGY ---
        strategy = "Wait & Watch"
        if "UPTREND" in trend and curr['RSI'] < 70: strategy = "Momentum Buy"
        if "UPTREND" in trend and curr['RSI'] < 40: strategy = "Pullback Buy"
        if "DOWNTREND" in trend: strategy = "Avoid / Short"
        
        # --- 5. AI & SENTIMENT ---
        ai_sig = get_ai_prediction(symbol, df)
        ai_verdict = "BUY" if ai_sig == 1 else "WAIT/SELL"
        sent_score, _ = news_bot.get_sentiment(symbol)
        
        sentiment_text = "Neutral"
        if sent_score > 0.2: sentiment_text = "Positive 🟢"
        if sent_score < -0.2: sentiment_text = "Negative 🔴"

        decision = "GOOD" if (ai_sig == 1 and "UPTREND" in trend) else "NOT GOOD"

        # --- 6. COST ANALYSIS ---
        costs = calculate_delivery_costs(float(curr['Close']), 10)

        # --- CONSTRUCT REPORT ---
        return {
            "symbol": symbol,
            "current_price": round(float(curr['Close']), 2),
            "trend": trend,
            "volume_strength": vol_strength,
            "ai_verdict": ai_verdict,
            "sentiment": sentiment_text,
            "strategy": strategy,
            "entry_zone": f"₹{round(curr['Close'] * 0.99, 2)} - ₹{round(curr['Close'] * 1.01, 2)}",
            "stop_loss": stop_loss,
            "target": target,
            "risk_reward": risk_reward,
            "decision": decision,
            "reason": f"Trend is {trend}, Volume is {vol_strength}, AI says {ai_verdict}",
            "total_tax": float(costs['total_charges']),
            "break_even": float(costs['net_price'])
        }

    except Exception as e:
        return {"error": str(e)}

def scan_market(sector="All"):
    print(f"🧠 Senior Quant Analyzing Sector: {sector}...")
    news_bot = NewsAnalyzer()
    
    stock_list = get_stocks_by_sector(sector)
    report = []

    for symbol in stock_list:
        try:
            df = fetch_data(symbol, period="1y")
            if df.empty: continue

            df = add_indicators(df)
            current = df.iloc[-1]
            prev = df.iloc[-2]
            
            score = 0
            reasons = []
            
            patterns = check_candlestick_patterns(df)
            if patterns:
                score += 15
                reasons.append(f"Pattern: {patterns[0]}")
            
            if current['ADX'] > 25:
                score += 10
                reasons.append(f"Strong Trend")
            
            if 30 < current['RSI'] < 70 and current['RSI'] > df.iloc[-2]['RSI']:
                score += 10
            elif current['RSI'] <= 30:
                score += 15
                reasons.append("Oversold")
                
            ai_signal = get_ai_prediction(symbol, df)
            if ai_signal == 1:
                score += 25
                reasons.append("AI Prediction: UP")
            
            sentiment, _ = news_bot.get_sentiment(symbol)
            if sentiment > 0.2:
                score += 15
                reasons.append("Positive News")

            costs = calculate_delivery_costs(float(current['Close']), 10) 

            confidence = min(100, score)
            
            entry = {
                "symbol": str(symbol),
                "price": round(float(current['Close']), 2),
                "score": round(float(confidence), 1),
                "ai_says": "BUY" if ai_signal == 1 else "WAIT",
                "reasons": " + ".join(reasons) if reasons else "Weak Technicals",
                "break_even": float(costs['net_price']),
                "total_tax": float(costs['total_charges']),
                "patterns": ", ".join(patterns) if patterns else "None",
                "indicators": f"ADX:{int(current['ADX'])} RSI:{int(current['RSI'])}"
            }

            breakout_signal = check_breakout(df)
            if breakout_signal == "Bullish Breakout 🚀":
                score += 25 # Huge bonus for breakouts
                reasons.append(f"Breakout! Price > 20-Day High")
            elif breakout_signal == "Bearish Breakdown 📉":
                score -= 25 # Avoid falling stocks
            
            if score > 15:
                report.append(entry)
                print(f"   🔎 {symbol}: Score {confidence}%")

        except Exception as e:
            # print(f"   ❌ Error {symbol}: {e}")
            pass

    if report:
        report = sorted(report, key=lambda x: x['score'], reverse=True)
        return report[0], report
    return None, []