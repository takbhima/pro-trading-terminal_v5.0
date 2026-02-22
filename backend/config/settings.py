"""
backend/config/settings.py - Application configuration

Centralized configuration for the trading system.
Environment-specific settings (dev, staging, production).
"""
from enum import Enum
from typing import Dict, Tuple
import os

class Environment(str, Enum):
    """Application environment."""
    DEV = "dev"
    STAGING = "staging"
    PRODUCTION = "prod"


class TimeFrame(str, Enum):
    """Supported timeframes."""
    M1 = "1m"
    M2 = "2m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H2 = "2h"
    D1 = "1d"
    W1 = "1wk"
    MO1 = "1mo"


class MarketName(str, Enum):
    """Market names."""
    NSE = "NSE"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    LSE = "LSE"


class Settings:
    """Main application settings."""
    
    # Environment
    ENV: Environment = Environment(os.getenv("APP_ENV", "dev"))
    
    # Server
    HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("APP_PORT", "8000"))
    RELOAD: bool = ENV == Environment.DEV
    
    # Data fetching
    DATA_FETCH_TIMEOUT: int = 20  # seconds
    DATA_FETCH_RETRIES: int = 3
    DATA_MIN_BARS: int = 50  # Minimum bars required for valid data
    
    # Cache
    CANDLE_CACHE_TTL: int = 300  # 5 minutes
    INDICATOR_CACHE_TTL: int = 60  # 1 minute
    NEWS_CACHE_TTL: int = 600  # 10 minutes
    
    # Strategy scanning
    SCAN_INTERVAL: int = 60  # seconds (every 60s)
    WATCHLIST_SCAN_LIMIT: int = 10  # Scan first 10 symbols
    
    # WebSocket
    WS_TICK_INTERVAL: int = 5  # seconds (send price every 5s)
    WS_STATUS_INTERVAL: int = 60  # seconds (send status every 60s)
    
    # Trading
    MAX_ACTIVE_TRADES_PER_SYMBOL: int = 1  # One trade per symbol
    EOD_EXIT_ENABLED: bool = True
    
    # News & Prediction
    NEWS_FETCH_COUNT: int = 10
    NEWS_MAX_AGE_DAYS: int = 7
    PREDICTION_MIN_BARS: int = 50
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # File paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    WATCHLIST_FILE: str = os.path.join(BASE_DIR, "watchlist.json")
    TRADES_LOG_FILE: str = os.path.join(BASE_DIR, "trades.json")
    
    @classmethod
    def is_dev(cls) -> bool:
        return cls.ENV == Environment.DEV
    
    @classmethod
    def is_prod(cls) -> bool:
        return cls.ENV == Environment.PRODUCTION


class MarketHours:
    """Market trading hours and timezones."""
    
    # Format: (timezone_str, (open_hour, open_minute), (close_hour, close_minute))
    HOURS: Dict[MarketName, Tuple[str, Tuple[int, int], Tuple[int, int]]] = {
        MarketName.NSE: ('Asia/Kolkata', (9, 15), (15, 30)),
        MarketName.NYSE: ('America/New_York', (9, 30), (16, 0)),
        MarketName.NASDAQ: ('America/New_York', (9, 30), (16, 0)),
        MarketName.LSE: ('Europe/London', (8, 0), (16, 30)),
    }
    
    # EOD exit times (hour, minute)
    EOD_CUTOFF: Dict[MarketName, Tuple[int, int]] = {
        MarketName.NSE: (15, 20),   # 3:20 PM IST
        MarketName.NYSE: (15, 55),  # 3:55 PM EST
    }
    
    # Crypto & futures (24/7)
    CRYPTO_SYMBOLS = {
        'BTC-USD', 'ETH-USD', 'BNB-USD', 'SOL-USD', 'XRP-USD',
        'DOGE-USD', 'GC=F', 'SI=F', 'CL=F', 'NG=F'
    }
    
    FUTURES_SUFFIX = '=F'


class IndicatorParams:
    """Default parameters for technical indicators."""
    
    # Moving Averages
    EMA_FAST: int = 9
    EMA_MEDIUM: int = 21
    EMA_SLOW: int = 50
    EMA_TREND: int = 200
    
    # Momentum
    RSI_PERIOD: int = 14
    RSI_OVERBOUGHT: float = 70.0
    RSI_OVERSOLD: float = 30.0
    RSI_NEUTRAL: float = 50.0
    
    # Volatility
    ATR_PERIOD: int = 14
    BOLLINGER_PERIOD: int = 20
    BOLLINGER_STD: float = 2.0
    
    # Trend
    SUPERTREND_FACTOR: float = 3.0
    SUPERTREND_PERIOD: int = 10
    
    SUPERTREND_SCALPER_FACTOR: float = 2.0
    SUPERTREND_SCALPER_PERIOD: int = 7
    
    # MACD
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9


class DataPeriodMap:
    """Period to fetch for each timeframe (for EMA 200 calculation)."""
    
    PERIODS: Dict[TimeFrame, str] = {
        TimeFrame.M1: "7d",
        TimeFrame.M2: "7d",
        TimeFrame.M5: "60d",
        TimeFrame.M15: "60d",
        TimeFrame.M30: "60d",
        TimeFrame.H1: "730d",
        TimeFrame.H2: "730d",
        TimeFrame.D1: "2y",
        TimeFrame.W1: "10y",
        TimeFrame.MO1: "10y",
    }
    
    @classmethod
    def get(cls, timeframe: str, default: str = "2y") -> str:
        """Get period for timeframe, with fallback."""
        try:
            tf = TimeFrame(timeframe)
            return cls.PERIODS.get(tf, default)
        except ValueError:
            return default


class TimeframeMinutes:
    """Convert timeframe to minutes."""
    
    MAP: Dict[str, int] = {
        '1m': 1, '2m': 2, '5m': 5, '15m': 15, '30m': 30,
        '60m': 60, '1h': 60, '2h': 120,
        '1d': 1440, '1wk': 10080, '1mo': 43200,
    }
    
    @classmethod
    def get(cls, timeframe: str, default: int = 60) -> int:
        """Get minutes for timeframe, with fallback."""
        return cls.MAP.get(timeframe, default)
