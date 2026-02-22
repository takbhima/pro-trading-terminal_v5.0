"""
backend/domain/strategies/pro_mtf.py - Pro MTF Strategy

EMA 9/21 crossover + RSI 50 + EMA 200 trend + Supertrend confirm
Best for: 1D, 1W swings (1-3 signals per day)
"""
from typing import List
import pandas as pd
from backend.domain.strategies.base import BaseStrategy
from backend.core.signal import Signal


class ProMTFStrategy(BaseStrategy):
    """
    Pro Multi-Timeframe Strategy
    
    Logic:
    - BUY: EMA 9 > EMA 21 (crossover) AND RSI > 50 AND Price > EMA 200 AND Supertrend bullish
    - SELL: EMA 9 < EMA 21 (crossunder) AND RSI < 50 AND Price < EMA 200 AND Supertrend bearish
    
    This is a conservative strategy that requires all conditions to align.
    Generates 1-3 signals per day on swing timeframes.
    """
    
    name = "Pro MTF"
    description = "EMA 9/21 cross + RSI + EMA 200 trend + Supertrend. Best for swing trading."
    signals_per_day_range = "1-3"
    best_for_timeframes = "1D, 1W"
    style = "Swing"
    color = "#3b82f6"
    
    def generate_signals(self, df: pd.DataFrame, ts_fn, symbol: str = "") -> List[Signal]:
        """
        Generate signals using Pro MTF logic.
        
        Expects df to have columns: Close, ema_9, ema_21, ema_200, rsi_14, atr_14, supertrend
        """
        if df is None or df.empty or len(df) < 2:
            return []
        
        # Ensure required columns exist
        required = ['Close', 'ema_9', 'ema_21', 'ema_200', 'rsi_14', 'atr_14', 
                    'crossover_9_21', 'crossunder_9_21', 'supertrend']
        for col in required:
            if col not in df.columns:
                return []
        
        signals = []
        c = df['Close']
        e9 = df['ema_9']
        e21 = df['ema_21']
        e200 = df['ema_200']
        r = df['rsi_14']
        a = df['atr_14']
        st = df['supertrend']
        cu = df['crossover_9_21']
        cd = df['crossunder_9_21']
        
        # Scan from bar 1 onward
        for i in range(1, len(df)):
            price = float(c.iloc[i])
            rsi_val = float(r.iloc[i])
            atr_val = float(a.iloc[i])
            
            # BUY signal
            if (cu.iloc[i] and                  # EMA 9 crosses above EMA 21
                rsi_val > 50 and                # RSI above neutral
                price > float(e200.iloc[i]) and # Price above EMA 200
                float(st.iloc[i]) < 0):         # Supertrend bullish
                
                sig = self._build_signal(df, i, 'BUY', atr_val, rsi_val,
                                       ts_fn, 'pro_mtf', symbol)
                signals.append(sig)
            
            # SELL signal
            elif (cd.iloc[i] and                 # EMA 9 crosses below EMA 21
                  rsi_val < 50 and               # RSI below neutral
                  price < float(e200.iloc[i]) and # Price below EMA 200
                  float(st.iloc[i]) > 0):         # Supertrend bearish
                
                sig = self._build_signal(df, i, 'SELL', atr_val, rsi_val,
                                       ts_fn, 'pro_mtf', symbol)
                signals.append(sig)
        
        return signals
