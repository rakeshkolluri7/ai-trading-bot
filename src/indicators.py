# src/indicators.py
import pandas as pd
import ta 

def add_indicators(df):
    """Calculates basic indicators using 'ta' library."""
    df = df.copy()
    
    # RSI
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # EMAs
    df['EMA_Fast'] = ta.trend.ema_indicator(df['Close'], window=8)
    df['EMA_Slow'] = ta.trend.ema_indicator(df['Close'], window=21)
    
    # MACD
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    
    # ATR
    df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['BB_High'] = bb.bollinger_hband()
    df['BB_Low'] = bb.bollinger_lband()

    # ADX
    adx = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close'], window=14)
    df['ADX'] = adx.adx()

    # --- VOLUME & MOMENTUM ---
    
    # VWAP (Volume Weighted Average Price)
    # Note: Traditional VWAP resets daily. If data is daily timeframe, this is just typical price * vol. 
    # For meaningful VWAP on daily charts, we usually use Rolling VWAP or Anchored VWAP.
    # Here we implement a Rolling VWAP (20 days) for swing/intraday hybrid view.
    cum_vol = df['Volume'].rolling(window=20).sum()
    cum_pv = (df['Close'] * df['Volume']).rolling(window=20).sum()
    df['VWAP'] = cum_pv / cum_vol
    
    # OBV (On Balance Volume)
    df['OBV'] = ta.volume.on_balance_volume(df['Close'], df['Volume'])

    # SuperTrend (Manual Implementation)
    high = df['High']
    low = df['Low']
    close = df['Close']
    atr = ta.volatility.average_true_range(high, low, close, window=10)
    multiplier = 3
    
    # Basic calculation
    hl2 = (high + low) / 2
    final_upperband = hl2 + (multiplier * atr)
    final_lowerband = hl2 - (multiplier * atr)
    
    # Recursive calculation for SuperTrend
    supertrend = [True] * len(df) # True = Green, False = Red
    st_values = [0.0] * len(df)
    
    for i in range(1, len(df)):
        if close.iloc[i] > final_upperband.iloc[i-1]:
            supertrend[i] = True
        elif close.iloc[i] < final_lowerband.iloc[i-1]:
            supertrend[i] = False
        else:
            supertrend[i] = supertrend[i-1] # Continue trend
            
            # Adjustment logic
            if supertrend[i] == True and final_lowerband.iloc[i] < final_lowerband.iloc[i-1]:
                final_lowerband.iloc[i] = final_lowerband.iloc[i-1]
            if supertrend[i] == False and final_upperband.iloc[i] > final_upperband.iloc[i-1]:
                final_upperband.iloc[i] = final_upperband.iloc[i-1]

        if supertrend[i]:
            st_values[i] = final_lowerband.iloc[i]
        else:
            st_values[i] = final_upperband.iloc[i]
            
    df['SuperTrend'] = st_values
    df['SuperTrend_Signal'] = supertrend # True=Buy Zone, False=Sell Zone
    
    # Stochastic
    stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
    df['Stoch_K'] = stoch.stoch()

    return df

def check_candlestick_patterns(df):
    """Checks for patterns using pure math (No pandas_ta required)."""
    # We need at least 3 candles to detect complex patterns
    recent = df.tail(3).copy()
    if len(recent) < 3: return []
    
    patterns_found = []
    
    # Candles: 0=DayBeforeYesterday, 1=Yesterday, 2=Today
    c0 = recent.iloc[0]
    c1 = recent.iloc[1]
    c2 = recent.iloc[2]
    
    # --- HELPER FUNCTIONS ---
    def body(c): return abs(c['Close'] - c['Open'])
    def is_green(c): return c['Close'] > c['Open']
    def is_red(c): return c['Close'] < c['Open']
    
    # --- 2-CANDLE PATTERNS ---
    
    # 1. Bullish Engulfing
    # Yesterday Red, Today Green, Today engulfs Yesterday
    if is_red(c1) and is_green(c2) and \
       (c2['Close'] > c1['Open']) and (c2['Open'] < c1['Close']):
        patterns_found.append("Bullish Engulfing")

    # 2. Bearish Engulfing
    # Yesterday Green, Today Red, Today engulfs Yesterday
    if is_green(c1) and is_red(c2) and \
       (c2['Open'] > c1['Close']) and (c2['Close'] < c1['Open']):
        patterns_found.append("Bearish Engulfing")

    # --- SINGLE CANDLE PATTERNS ---

    # 3. Hammer (Bullish Reversal)
    # Long lower wick (2x body), small upper wick
    lower_wick = min(c2['Close'], c2['Open']) - c2['Low']
    upper_wick = c2['High'] - max(c2['Close'], c2['Open'])
    
    if (lower_wick > 2 * body(c2)) and (upper_wick < body(c2) * 0.5):
        patterns_found.append("Hammer")

    # 4. Shooting Star (Bearish Reversal)
    # Long upper wick (2x body), small lower wick
    if (upper_wick > 2 * body(c2)) and (lower_wick < body(c2) * 0.5):
        patterns_found.append("Shooting Star")

    # --- 3-CANDLE PATTERNS ---

    # 5. Morning Star (Bullish Reversal)
    # Big Red -> Small Body (Gap Down) -> Big Green (Gap Up)
    if is_red(c0) and is_green(c2) and \
       (body(c0) > body(c1) * 2) and \
       (c2['Close'] > (c0['Open'] + c0['Close'])/2): 
        patterns_found.append("Morning Star")

    # 6. Evening Star (Bearish Reversal)
    # Big Green -> Small Body (Gap Up) -> Big Red (Gap Down)
    if is_green(c0) and is_red(c2) and \
       (body(c0) > body(c1) * 2) and \
       (c2['Close'] < (c0['Open'] + c0['Close'])/2):
        patterns_found.append("Evening Star")

    return patterns_found

# ... (Keep existing imports and functions) ...

def check_breakout(df, window=20):
    """
    Checks if the stock is breaking out of a 20-day range.
    Returns: 'Bullish Breakout', 'Bearish Breakdown', or None
    """
    # 1. Calculate the Range (Donchian Channels)
    # We look at the last 'window' days EXCLUDING today
    past_high = df['High'].rolling(window=window).max().shift(1).iloc[-1]
    past_low = df['Low'].rolling(window=window).min().shift(1).iloc[-1]
    
    # 2. Get Today's Data
    curr_close = df['Close'].iloc[-1]
    curr_vol = df['Volume'].iloc[-1]
    avg_vol = df['Volume'].rolling(window=20).mean().iloc[-1]
    
    # 3. Check for Bullish Breakout (Price > High AND Volume > Average)
    if curr_close > past_high and curr_vol > avg_vol:
        return "Bullish Breakout 🚀"
    
    # 4. Check for Bearish Breakdown (Price < Low AND Volume > Average)
    if curr_close < past_low and curr_vol > avg_vol:
        return "Bearish Breakdown 📉"
        
    return None