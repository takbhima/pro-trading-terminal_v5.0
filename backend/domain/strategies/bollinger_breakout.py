"""
backend/domain/strategies/bollinger_breakout.py - Bollinger Breakout Strategy

Price breaks Bollinger Band + RSI + volume confirmation
Best for: Momentum breakouts (4-6 signals per day)
"""
from typing import List
import pandas as pd
from backend.domain.strategies.base import BaseStrategy
from backend.core.signal import Signal


class BollingerBreakoutStrategy(BaseStrategy):
    """
    Bollinger Breakout Strategy
    
    Logic:
    - BUY: Price breaks above upper BB AND RSI > 55 AND Volume > 1.3x average
    - SELL: Price breaks below lower BB AND RSI < 45 AND Volume > 1.3x average
    
    Generates 4-6 signals per day on intraday timeframes.
    """
    
    name = "Bollinger Breakout"
    description = "Price breaks Bollinger Band + RSI momentum + volume spike confirmation."
    signals_per_day_range = "4-6"
    best_for_timeframes = "5m, 15m"
    style = "Breakout"
    color = "#f0b429"
    
    def generate_signals(self, df: pd.DataFrame, ts_fn, symbol: str = "") -> List[Signal]:
        """
        Generate signals using Bollinger Breakout logic.
        
        Expects df to have columns: Close, High, Low, Volume, rsi_14, atr_14
        """
        if df is None or df.empty or len(df) < 20:
            return []
        
        # Ensure required columns exist
        required = ['Close', 'Volume', 'rsi_14', 'atr_14']
        for col in required:
            if col not in df.columns:
                return []
        
        # Calculate Bollinger Bands if not present
        if 'bb_upper' not in df.columns or 'bb_lower' not in df.columns:
            df = df.copy()
            sma = df['Close'].rolling(20).mean()
            std = df['Close'].rolling(20).std()
            df['bb_upper'] = sma + 2 * std
            df['bb_lower'] = sma - 2 * std
        
        signals = []
        c = df['Close']
        r = df['rsi_14']
        a = df['atr_14']
        v = df['Volume']
        vm = v.rolling(20).mean()
        
        # Previous values for crossover detection
        c_prev = c.shift(1)
        up_prev = df['bb_upper'].shift(1)
        lo_prev = df['bb_lower'].shift(1)
        
        # Scan from bar 20 onward (need 20 bars for BB)
        for i in range(20, len(df)):
            price = float(c.iloc[i])
            rsi_val = float(r.iloc[i])
            atr_val = float(a.iloc[i])
            vol_ok = float(v.iloc[i]) > float(vm.iloc[i]) * 1.3
            
            # BUY signal: break above upper BB
            if (float(c_prev.iloc[i]) <= float(up_prev.iloc[i]) and
                price > float(df['bb_upper'].iloc[i]) and
                rsi_val > 55 and vol_ok):
                
                sig = self._build_signal(df, i, 'BUY', atr_val, rsi_val,
                                       ts_fn, 'bollinger_breakout', symbol)
                signals.append(sig)
            
            # SELL signal: break below lower BB
            elif (float(c_prev.iloc[i]) >= float(lo_prev.iloc[i]) and
                  price < float(df['bb_lower'].iloc[i]) and
                  rsi_val < 45 and vol_ok):
                
                sig = self._build_signal(df, i, 'SELL', atr_val, rsi_val,
                                       ts_fn, 'bollinger_breakout', symbol)
                signals.append(sig)
        
        return signals
