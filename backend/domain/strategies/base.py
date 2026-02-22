"""
backend/domain/strategies/base.py - Abstract strategy base class

Uses Template Method Pattern:
- Subclasses implement generate_signals(df)
- BaseStrategy handles common logic (signal building, confidence calculation)
"""
from abc import ABC, abstractmethod
from typing import List
import pandas as pd
from backend.core.signal import Signal
from backend.config.settings import IndicatorParams


class BaseStrategy(ABC):
    """
    Abstract base for all trading strategies.
    
    Subclasses must implement:
        - name: Strategy display name
        - description: Strategy description
        - signals_per_day_range: "1-3" format
        - best_for_timeframes: "5m, 15m" format
        - generate_signals(df, ts_fn): Return list of signals
    
    The run() method orchestrates the signal generation pipeline.
    """
    
    # Metadata (override in subclasses)
    name: str = "Base Strategy"
    description: str = "Base class for trading strategies"
    signals_per_day_range: str = "1-3"
    best_for_timeframes: str = "5m, 15m, 1h"
    style: str = "General"
    color: str = "#888888"
    
    def __init__(self):
        """Initialize strategy."""
        pass
    
    def run(self, df: pd.DataFrame, ts_fn, symbol: str = "") -> List[Signal]:
        """
        Run the strategy on OHLCV data.
        
        Template method: orchestrates the pipeline
        
        Args:
            df: OHLCV DataFrame with indicators pre-calculated
            ts_fn: Timestamp formatting function
            symbol: Trading symbol
        
        Returns:
            List of Signal objects
        """
        if df is None or df.empty:
            return []
        
        # Call subclass implementation
        return self.generate_signals(df, ts_fn, symbol)
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame, ts_fn, symbol: str) -> List[Signal]:
        """
        Generate signals from OHLCV data.
        
        Subclasses implement this method with their specific logic.
        
        Args:
            df: OHLCV DataFrame with indicators
            ts_fn: Timestamp formatting function
            symbol: Trading symbol
        
        Returns:
            List of Signal objects
        """
        pass
    
    # ─────────────────────────────────────────────────────────────
    # Helper methods for building signals (DRY principle)
    # ─────────────────────────────────────────────────────────────
    
    @staticmethod
    def _build_signal(df: pd.DataFrame, i: int, signal_type: str,
                      atr_value: float, rsi_value: float,
                      ts_fn, strategy_key: str, symbol: str = "") -> Signal:
        """
        Build a complete signal object.
        
        Common logic for all strategies:
        - Extract OHLCV at index i
        - Calculate confidence from RSI distance from neutral (50)
        - Build SL and TP based on ATR
        - Return Signal object
        
        Args:
            df: DataFrame with Close, High, Low, Volume
            i: Bar index
            signal_type: 'BUY' or 'SELL'
            atr_value: ATR value at this bar
            rsi_value: RSI value at this bar
            ts_fn: Timestamp formatter
            strategy_key: Strategy identifier
            symbol: Trading symbol (optional)
        
        Returns:
            Signal object
        """
        close = float(df['Close'].iloc[i])
        
        # Confidence: based on RSI distance from neutral (50)
        # BUY: closer to 100 = higher confidence
        # SELL: closer to 0 = higher confidence
        dist = max(0.0, (rsi_value - 50.0) if signal_type == 'BUY' else (50.0 - rsi_value))
        confidence = round(min(95.0, 50.0 + dist * 1.8), 1)
        
        # Stop Loss & Take Profit based on ATR
        if signal_type == 'BUY':
            sl = round(close - atr_value, 4)
            tp = round(close + atr_value * 2.0, 4)
        else:  # SELL
            sl = round(close + atr_value, 4)
            tp = round(close - atr_value * 2.0, 4)
        
        return Signal(
            type=signal_type,
            symbol=symbol,
            price=round(close, 4),
            sl=sl,
            tp=tp,
            rsi=round(rsi_value, 2),
            atr=round(atr_value, 4),
            confidence=confidence,
            strategy=strategy_key,
            time=int(ts_fn(df.index[i])),
        )
    
    @staticmethod
    def _rsi_distance_from_neutral(rsi: float) -> float:
        """
        Calculate distance from RSI neutral (50).
        Used for confidence scoring.
        
        Args:
            rsi: RSI value (0-100)
        
        Returns:
            Distance from 50
        """
        return abs(rsi - 50.0)
    
    @staticmethod
    def _is_price_between(price: float, lower: float, upper: float) -> bool:
        """Check if price is between lower and upper."""
        return lower < price < upper
    
    @staticmethod
    def _is_series_between(series: pd.Series, lower: pd.Series, upper: pd.Series) -> pd.Series:
        """Check if series values are between bounds element-wise."""
        return (series > lower) & (series < upper)
    
    def metadata(self) -> dict:
        """Return strategy metadata."""
        return {
            'key': self.__class__.__name__.lower(),
            'name': self.name,
            'description': self.description,
            'signals_day': self.signals_per_day_range,
            'best_for': self.best_for_timeframes,
            'style': self.style,
            'color': self.color,
        }
