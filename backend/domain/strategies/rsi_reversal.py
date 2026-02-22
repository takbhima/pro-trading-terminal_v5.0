"""
backend/domain/strategies/rsi_reversal.py - RSI Reversal Strategy

RSI exits oversold/overbought + EMA 50 trend filter
Best for: Intraday mean reversion (3-6 signals per day)
"""
from typing import List
import pandas as pd
from backend.domain.strategies.base import BaseStrategy
from backend.core.signal import Signal


class RSIReversalStrategy(BaseStrategy):
    """
    RSI Reversal Strategy
    
    Logic:
    - BUY: RSI crosses above 30 (exit oversold) AND Price > EMA 50
    - SELL: RSI crosses below 70 (exit overbought) AND Price < EMA 50
    
    Generates 3-6 signals per day on intraday timeframes.
    """
    
    name = "RSI Reversal"
    description = "RSI exits oversold (<30) or overbought (>70) zones with EMA 50 filter."
    signals_per_day_range = "3-6"
    best_for_timeframes = "5m, 15m"
    style = "Mean Reversion"
    color = "#a78bfa"
    
    def generate_signals(self, df: pd.DataFrame, ts_fn, symbol: str = "") -> List[Signal]:
        """
        Generate signals using RSI Reversal logic.
        
        Expects df to have columns: Close, rsi_14, atr_14, and optionally ema_50
        """
        if df is None or df.empty or len(df) < 2:
            return []
        
        # Ensure required columns exist
        required = ['Close', 'rsi_14', 'atr_14']
        for col in required:
            if col not in df.columns:
                return []
        
        # Add EMA 50 if not present
        if 'ema_50' not in df.columns:
            from backend.domain.indicators import ema
            df = df.copy()
            df['ema_50'] = ema(df['Close'], 50)
        
        signals = []
        c = df['Close']
        r = df['rsi_14']
        a = df['atr_14']
        e50 = df['ema_50']
        r_prev = r.shift(1).fillna(50)
        
        # RSI crosses 30 upward (exit oversold → BUY)
        cross30_up = (r_prev < 30) & (r >= 30)
        # RSI crosses 70 downward (exit overbought → SELL)
        cross70_down = (r_prev > 70) & (r <= 70)
        
        # Scan from bar 1 onward
        for i in range(1, len(df)):
            price = float(c.iloc[i])
            rsi_val = float(r.iloc[i])
            atr_val = float(a.iloc[i])
            e50_val = float(e50.iloc[i])
            
            # BUY signal
            if cross30_up.iloc[i] and price > e50_val:
                sig = self._build_signal(df, i, 'BUY', atr_val, rsi_val,
                                       ts_fn, 'rsi_reversal', symbol)
                signals.append(sig)
            
            # SELL signal
            elif cross70_down.iloc[i] and price < e50_val:
                sig = self._build_signal(df, i, 'SELL', atr_val, rsi_val,
                                       ts_fn, 'rsi_reversal', symbol)
                signals.append(sig)
        
        return signals
