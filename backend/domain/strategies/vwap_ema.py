"""
backend/domain/strategies/vwap_ema.py - VWAP + EMA Strategy

Price vs VWAP crossover + EMA 9/21 direction + RSI momentum
Best for: Intraday (4-6 signals per day)
"""
from typing import List
import pandas as pd
import numpy as np
from backend.domain.strategies.base import BaseStrategy
from backend.core.signal import Signal


class VWAPEMAStrategy(BaseStrategy):
    """
    VWAP + EMA Strategy
    
    Logic:
    - BUY: Price crosses above VWAP AND EMA 9 > EMA 21 AND RSI > 50
    - SELL: Price crosses below VWAP AND EMA 9 < EMA 21 AND RSI < 50
    
    Generates 4-6 signals per day on intraday timeframes.
    """
    
    name = "VWAP + EMA"
    description = "Price vs VWAP crossover + EMA 9/21 direction + RSI. Classic intraday."
    signals_per_day_range = "4-6"
    best_for_timeframes = "5m, 15m"
    style = "Intraday"
    color = "#00d084"
    
    def generate_signals(self, df: pd.DataFrame, ts_fn, symbol: str = "") -> List[Signal]:
        """
        Generate signals using VWAP + EMA logic.
        
        Expects df to have columns: Close, Volume, ema_9, ema_21, rsi_14, atr_14
        """
        if df is None or df.empty or len(df) < 2:
            return []
        
        # Calculate VWAP
        try:
            tp = (df['High'] + df['Low'] + df['Close']) / 3
            vwap = (tp * df['Volume']).cumsum() / df['Volume'].replace(0, np.nan).cumsum()
        except Exception:
            return []
        
        # Ensure required columns exist
        required = ['Close', 'ema_9', 'ema_21', 'rsi_14', 'atr_14']
        for col in required:
            if col not in df.columns:
                return []
        
        signals = []
        c = df['Close']
        e9 = df['ema_9']
        e21 = df['ema_21']
        r = df['rsi_14']
        a = df['atr_14']
        
        # VWAP crossovers
        c_prev = c.shift(1)
        vwap_prev = vwap.shift(1)
        cv_up = (c_prev <= vwap_prev) & (c > vwap)
        cv_dn = (c_prev >= vwap_prev) & (c < vwap)
        
        # Scan from bar 1 onward
        for i in range(1, len(df)):
            price = float(c.iloc[i])
            rsi_val = float(r.iloc[i])
            atr_val = float(a.iloc[i])
            e9_val = float(e9.iloc[i])
            e21_val = float(e21.iloc[i])
            
            # BUY signal
            if cv_up.iloc[i] and e9_val > e21_val and rsi_val > 50:
                sig = self._build_signal(df, i, 'BUY', atr_val, rsi_val,
                                       ts_fn, 'vwap_ema', symbol)
                signals.append(sig)
            
            # SELL signal
            elif cv_dn.iloc[i] and e9_val < e21_val and rsi_val < 50:
                sig = self._build_signal(df, i, 'SELL', atr_val, rsi_val,
                                       ts_fn, 'vwap_ema', symbol)
                signals.append(sig)
        
        return signals
