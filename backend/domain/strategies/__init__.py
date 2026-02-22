"""
backend/domain/strategies/__init__.py - Strategy Registry and Factory

Factory Pattern Implementation:
- STRATEGY_REGISTRY: Central registration of all strategies
- StrategyFactory: Instantiate strategies by key
- add_strategy(): Register new strategies at runtime
- list_strategies(): Get metadata for all registered strategies

Benefits:
- Adding new strategies doesn't require modifying this file
- Easy to enable/disable strategies
- Strategies can be loaded dynamically from plugins
"""
from typing import Dict, Type, List, Optional
from backend.domain.strategies.base import BaseStrategy
from backend.domain.strategies.pro_mtf import ProMTFStrategy
from backend.domain.strategies.vwap_ema import VWAPEMAStrategy
from backend.domain.strategies.rsi_reversal import RSIReversalStrategy
from backend.domain.strategies.bollinger_breakout import BollingerBreakoutStrategy
from backend.domain.strategies.macd_crossover import MACDCrossoverStrategy
from backend.domain.strategies.supertrend_scalper import SupertrendScalperStrategy


class StrategyRegistry:
    """
    Central registry for all strategies.
    Uses Factory Pattern to create strategy instances by key.
    """
    
    _strategies: Dict[str, Type[BaseStrategy]] = {}
    
    @classmethod
    def register(cls, key: str, strategy_class: Type[BaseStrategy]) -> None:
        """
        Register a strategy class.
        
        Args:
            key: Unique strategy identifier (e.g., 'pro_mtf')
            strategy_class: Strategy class (must extend BaseStrategy)
        """
        if not issubclass(strategy_class, BaseStrategy):
            raise TypeError(f"{strategy_class} must extend BaseStrategy")
        cls._strategies[key] = strategy_class
    
    @classmethod
    def get(cls, key: str) -> Optional[BaseStrategy]:
        """
        Get a strategy instance by key.
        
        Args:
            key: Strategy identifier
        
        Returns:
            Strategy instance or None if not registered
        """
        if key not in cls._strategies:
            return None
        return cls._strategies[key]()
    
    @classmethod
    def all_keys(cls) -> List[str]:
        """Get all registered strategy keys."""
        return list(cls._strategies.keys())
    
    @classmethod
    def all_strategies(cls) -> Dict[str, BaseStrategy]:
        """Get all strategies as {key: instance}."""
        return {key: cls._strategies[key]() for key in cls._strategies}
    
    @classmethod
    def metadata_all(cls) -> List[dict]:
        """Get metadata for all registered strategies."""
        return [cls.get(key).metadata() for key in cls.all_keys()]
    
    @classmethod
    def is_registered(cls, key: str) -> bool:
        """Check if a strategy is registered."""
        return key in cls._strategies


# ─────────────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────────────

def _register_default_strategies():
    """Register all default strategies."""
    StrategyRegistry.register('pro_mtf', ProMTFStrategy)
    StrategyRegistry.register('vwap_ema', VWAPEMAStrategy)
    StrategyRegistry.register('rsi_reversal', RSIReversalStrategy)
    StrategyRegistry.register('bollinger_breakout', BollingerBreakoutStrategy)
    StrategyRegistry.register('macd_crossover', MACDCrossoverStrategy)
    StrategyRegistry.register('supertrend_scalper', SupertrendScalperStrategy)


# Auto-register on module import
_register_default_strategies()


# ─────────────────────────────────────────────────────────────────────
# Public API (backward compatible with old code)
# ─────────────────────────────────────────────────────────────────────

STRATEGIES: Dict[str, dict] = {}

def _build_strategies_dict():
    """Build STRATEGIES dict for backward compatibility."""
    global STRATEGIES
    STRATEGIES = {}
    for key in StrategyRegistry.all_keys():
        strategy = StrategyRegistry.get(key)
        STRATEGIES[key] = {
            'fn': lambda df, ts, s=key: StrategyRegistry.get(s).run(df, ts),
            'name': strategy.name,
            'description': strategy.description,
            'signals_day': strategy.signals_per_day_range,
            'best_for': strategy.best_for_timeframes,
            'style': strategy.style,
            'color': strategy.color,
        }

_build_strategies_dict()


def list_strategies() -> List[dict]:
    """
    Get list of all strategies with metadata.
    
    Returns:
        List of {key, name, description, signals_day, best_for, style, color}
    """
    return [
        {
            'key': key,
            'name': strategy.name,
            'description': strategy.description,
            'signals_day': strategy.signals_per_day_range,
            'best_for': strategy.best_for_timeframes,
            'style': strategy.style,
            'color': strategy.color,
        }
        for key, strategy in StrategyRegistry.all_strategies().items()
    ]
