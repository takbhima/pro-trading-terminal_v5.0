"""
backend/core/trade.py - Trade lifecycle model

Manages trade state (ACTIVE → CLOSED) with exit reasons.
"""
from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
from datetime import datetime
from backend.core.signal import Signal


ExitReason = Literal['Target Hit', 'Stop Hit', 'Time Exit', 'EOD Exit', 'Manual Close']


@dataclass
class Trade:
    """
    Represents a single active trade.
    
    Attributes:
        symbol: Trading symbol
        side: 'BUY' or 'SELL'
        entry_price: Entry price
        target_price: Take profit level
        stop_loss: Stop loss level
        entry_time: When trade was opened (ISO format string)
        entry_time_dt: Python datetime (internal, not serialized)
        timeframe: Trading interval ('5m', '15m', '1d', etc.)
        strategy: Strategy name
        confidence: Signal confidence (0-100)
        expected_time_minutes: Estimated time to target
        expected_bars: Estimated bars to target
        rsi: RSI at entry
        atr: ATR at entry
        status: 'ACTIVE' or 'CLOSED'
        exit_price: Exit price (if closed)
        exit_reason: Why trade was closed (if closed)
        pnl: Profit/Loss in currency
        pnl_pct: Profit/Loss in %
        exit_time: When trade was closed (if closed)
    """
    
    symbol: str
    side: Literal['BUY', 'SELL']
    entry_price: float
    target_price: float
    stop_loss: float
    timeframe: str
    strategy: str
    confidence: float
    expected_time_minutes: float = 60.0
    expected_bars: float = 12.0
    rsi: float = 50.0
    atr: float = 0.0
    entry_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    entry_time_dt: datetime = field(default_factory=datetime.utcnow, repr=False)
    status: Literal['ACTIVE', 'CLOSED'] = 'ACTIVE'
    exit_price: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    exit_time: Optional[str] = None
    
    def __post_init__(self):
        """Validate trade integrity."""
        assert self.side in ('BUY', 'SELL'), f"Invalid side: {self.side}"
        if self.side == 'BUY':
            assert self.stop_loss < self.entry_price < self.target_price, \
                f"BUY: SL({self.stop_loss}) < Entry({self.entry_price}) < TP({self.target_price})"
        else:
            assert self.target_price < self.entry_price < self.stop_loss, \
                f"SELL: TP({self.target_price}) < Entry({self.entry_price}) < SL({self.stop_loss})"
    
    @classmethod
    def from_signal(cls, signal: Signal, timeframe: str) -> 'Trade':
        """Create a trade from a signal."""
        return cls(
            symbol=signal.symbol,
            side=signal.type,
            entry_price=signal.price,
            target_price=signal.tp,
            stop_loss=signal.sl,
            timeframe=timeframe,
            strategy=signal.strategy,
            confidence=signal.confidence,
            expected_bars=signal.target_bars or 12.0,
            rsi=signal.rsi,
            atr=signal.atr,
        )
    
    def close(self, exit_price: float, reason: ExitReason) -> None:
        """Close the trade and calculate P&L."""
        self.status = 'CLOSED'
        self.exit_price = round(exit_price, 4)
        self.exit_reason = reason
        self.exit_time = datetime.utcnow().isoformat()
        
        # Calculate P&L
        if self.side == 'BUY':
            self.pnl = round(exit_price - self.entry_price, 4)
        else:
            self.pnl = round(self.entry_price - exit_price, 4)
        
        if self.entry_price > 0:
            self.pnl_pct = round((self.pnl / self.entry_price) * 100, 2)
    
    @property
    def elapsed_minutes(self) -> float:
        """Minutes since trade opened."""
        delta = datetime.utcnow() - self.entry_time_dt
        return round(delta.total_seconds() / 60, 1)
    
    @property
    def is_active(self) -> bool:
        """True if trade is still open."""
        return self.status == 'ACTIVE'
    
    @property
    def is_profitable(self) -> bool:
        """True if P&L is positive."""
        return self.pnl is not None and self.pnl > 0
    
    def to_dict(self, include_internal: bool = False) -> dict:
        """Convert to dict for JSON serialization."""
        d = asdict(self)
        if not include_internal:
            d.pop('entry_time_dt', None)
        
        # Add computed properties
        if self.status == 'ACTIVE':
            d['elapsed_minutes'] = self.elapsed_minutes
        
        return d
    
    def check_target_hit(self, current_price: float) -> bool:
        """Check if target has been reached."""
        if self.side == 'BUY':
            return current_price >= self.target_price
        else:
            return current_price <= self.target_price
    
    def check_stop_hit(self, current_price: float) -> bool:
        """Check if stop loss has been breached."""
        if self.side == 'BUY':
            return current_price <= self.stop_loss
        else:
            return current_price >= self.stop_loss
    
    def compute_live_pnl(self, current_price: float) -> float:
        """Compute live P&L at current price (for ACTIVE trades)."""
        if not self.is_active:
            return self.pnl or 0.0
        
        if self.side == 'BUY':
            return round(current_price - self.entry_price, 4)
        else:
            return round(self.entry_price - current_price, 4)
