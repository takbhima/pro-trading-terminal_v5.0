"""
backend/domain/strategies/macd_crossover.py - MACD Crossover Strategy

MACD/Signal cross + histogram confirm + RSI filter
Best for: Trend trading (4-6 signals per day)
"""
from typing import List
import pandas as pd
from backend.domain.strategies.base import BaseStrategy
from backend.core.signal import Signal


class MACDCrossoverStrategy(BaseStrategy):
    """
    MACD Crossover Strategy
    
    Logic:
    - BUY: MACD crosses above Signal line AND histogram > 0 AND RSI > 50
    - SELL: MACD crosses below Signal line AND histogram < 0 AND RSI < 50
    
    Generates 4-6 signals per day on intraday-to-hourly timeframes.
    """
    
    name = "MACD Crossover"
    description = "MACD crosses Signal line + histogram confirms + RSI filter."
    signals_per_day_range = "4-6"
    best_for_timeframes = "15m, 1H"
    style = "Trend"
    color = "#fb7185"
    
    def generate_signals(self, df: pd.DataFrame, ts_fn, symbol: str = "") -> List[Signal]:
        """
        Generate signals using MACD Crossover logic.
        
        Expects df to have columns: Close, rsi_14, atr_14
        MACD, signal, and histogram will be calculated if not present
        """
        if df is None or df.empty or len(df) < 26:
            return []
        
        # Ensure required columns exist
        required = ['Close', 'rsi_14', 'atr_14']
        for col in required:
            if col not in df.columns:
                return []
        
        # Calculate MACD if not present
        if 'macd' not in df.columns or 'macd_signal' not in df.columns or 'macd_hist' not in df.columns:
            from backend.domain.indicators import ema
            df = df.copy()
            c = df['Close']
            macd_line = ema(c, 12) - ema(c, 26)
            macd_signal = ema(macd_line, 9)
            df['macd'] = macd_line
            df['macd_signal'] = macd_signal
            df['macd_hist'] = macd_line - macd_signal
        
        signals = []
        c = df['Close']
        r = df['rsi_14']
        a = df['atr_14']
        macd = df['macd']
        sig = df['macd_signal']
        hist = df['macd_hist']
        
        # Previous values for crossover detection
        macd_prev = macd.shift(1)
        sig_prev = sig.shift(1)
        
        # Scan from bar 1 onward
        for i in range(1, len(df)):
            price = float(c.iloc[i])
            rsi_val = float(r.iloc[i])
            atr_val = float(a.iloc[i])
            macd_val = float(macd.iloc[i])
            sig_val = float(sig.iloc[i])
            hist_val = float(hist.iloc[i])
            macd_prev_val = float(macd_prev.iloc[i])
            sig_prev_val = float(sig_prev.iloc[i])
            
            # BUY signal: MACD crosses above Signal
            if (macd_prev_val <= sig_prev_val and macd_val > sig_val and
                hist_val > 0 and rsi_val > 50):
                
                sig_obj = self._build_signal(df, i, 'BUY', atr_val, rsi_val,
                                           ts_fn, 'macd_crossover', symbol)
                signals.append(sig_obj)
            
            # SELL signal: MACD crosses below Signal
            elif (macd_prev_val >= sig_prev_val and macd_val < sig_val and
                  hist_val < 0 and rsi_val < 50):
                
                sig_obj = self._build_signal(df, i, 'SELL', atr_val, rsi_val,
                                           ts_fn, 'macd_crossover', symbol)
                signals.append(sig_obj)
        
        return signals
