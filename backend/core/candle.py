"""
backend/core/candle.py - Immutable OHLCV candle model

Represents a single candlestick with OHLCV data.
No external dependencies - pure data model.
"""
from dataclasses import dataclass
from typing import Optional, Union
from datetime import datetime


@dataclass(frozen=True)  # Immutable - prevents accidental modifications
class Candle:
    """Represents a single candlestick (OHLCV)."""
    
    time: Union[int, str, datetime]  # Unix timestamp or datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    
    def __post_init__(self):
        """Validate candle integrity."""
        assert self.high >= self.low, f"High {self.high} < Low {self.low}"
        assert self.high >= self.open, f"High {self.high} < Open {self.open}"
        assert self.high >= self.close, f"High {self.high} < Close {self.close}"
        assert self.low <= self.open, f"Low {self.low} > Open {self.open}"
        assert self.low <= self.close, f"Low {self.low} > Close {self.close}"
        assert self.open >= 0 and self.close >= 0, "Prices must be positive"
        
    def __dict__(self) -> dict:
        """Convert to dict for JSON serialization."""
        return {
            'time': int(self.time) if isinstance(self.time, (int, float)) else str(self.time),
            'open': round(self.open, 4),
            'high': round(self.high, 4),
            'low': round(self.low, 4),
            'close': round(self.close, 4),
            'volume': round(self.volume, 2),
        }
    
    @property
    def range(self) -> float:
        """High - Low range."""
        return self.high - self.low
    
    @property
    def body(self) -> float:
        """Absolute difference between open and close."""
        return abs(self.close - self.open)
    
    @property
    def is_bullish(self) -> bool:
        """True if close > open."""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """True if close < open."""
        return self.close < self.open
    
    @property
    def change_pct(self) -> float:
        """% change from open to close."""
        if self.open <= 0:
            return 0.0
        return round(((self.close - self.open) / self.open) * 100, 2)
