"""
backend/domain/strategies/supertrend_scalper.py - Supertrend Scalper Strategy

Fast Supertrend(2,7) flip with RSI confirmation
Best for: Aggressive scalping (6-12 signals per day)
"""
from typing import List
import pandas as pd
from backend.domain.strategies.base import BaseStrategy
from backend.core.signal import Signal


class SupertrendScalperStrategy(BaseStrategy):
    """
    Supertrend Scalper Strategy
    
    Logic:
    - BUY: Supertrend flips bullish (from +1 to -1) AND RSI > 45
    - SELL: Supertrend flips bearish (from -1 to +1) AND RSI < 55
    
    Uses aggressive parameters: factor=2.0, period=7
    Generates 6-12 signals per day on 5-minute timeframes.
    """
    
    name = "ST Scalper"
    description = "Fast Supertrend(2,7) direction flip + RSI confirmation. Most signals."
    signals_per_day_range = "6-12"
    best_for_timeframes = "5m"
    style = "Scalping"
    color = "#f97316"
    
    def generate_signals(self, df: pd.DataFrame, ts_fn, symbol: str = "") -> List[Signal]:
        """
        Generate signals using Supertrend Scalper logic.
        
        Expects df to have columns: Close, High, Low, rsi_14, atr_14
        """
        if df is None or df.empty or len(df) < 2:
            return []
        
        # Ensure required columns exist
        required = ['Close', 'High', 'Low', 'rsi_14', 'atr_14']
        for col in required:
            if col not in df.columns:
                return []
        
        # Calculate Supertrend with scalper parameters if not present
        if 'supertrend_scalper' not in df.columns:
            from backend.domain.indicators import supertrend
            df = df.copy()
            st_scalper = supertrend(df['High'], df['Low'], df['Close'], 
                                   factor=2.0, atr_len=7)
            df['supertrend_scalper'] = st_scalper
        
        signals = []
        c = df['Close']
        r = df['rsi_14']
        a = df['atr_14']
        st = df['supertrend_scalper']
        st_prev = st.shift(1)
        
        # Scan from bar 1 onward
        for i in range(1, len(df)):
            price = float(c.iloc[i])
            rsi_val = float(r.iloc[i])
            atr_val = float(a.iloc[i])
            st_val = float(st.iloc[i])
            st_prev_val = float(st_prev.iloc[i])
            
            # BUY signal: Supertrend flips from bearish (+1) to bullish (-1)
            if st_prev_val > 0 and st_val < 0 and rsi_val > 45:
                sig = self._build_signal(df, i, 'BUY', atr_val, rsi_val,
                                       ts_fn, 'supertrend_scalper', symbol)
                signals.append(sig)
            
            # SELL signal: Supertrend flips from bullish (-1) to bearish (+1)
            elif st_prev_val < 0 and st_val > 0 and rsi_val < 55:
                sig = self._build_signal(df, i, 'SELL', atr_val, rsi_val,
                                       ts_fn, 'supertrend_scalper', symbol)
                signals.append(sig)
        
        return signals
