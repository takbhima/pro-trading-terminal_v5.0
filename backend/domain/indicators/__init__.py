"""
backend/domain/indicators/__init__.py - All technical indicators in one module

This module contains all indicator calculations.
Each indicator is a pure function taking a pandas Series and returning a Series.

Functions:
    - ema(series, length) → EMA
    - sma(series, length) → SMA
    - rsi(series, length) → RSI
    - atr(high, low, close, length) → ATR
    - supertrend(high, low, close, factor, atr_len) → Supertrend direction (-1/+1)
    - macd(close, fast, slow, signal) → (macd_line, signal_line, histogram)
    - bollinger_bands(close, period, std_dev) → (upper, middle, lower)
    - crossover(series1, series2) → Boolean series
    - crossunder(series1, series2) → Boolean series
    - apply_indicators(df) → df with all indicators computed
"""
import pandas as pd
import numpy as np
from typing import Tuple


# ─────────────────────────────────────────────────────────────────────
# Moving Averages
# ─────────────────────────────────────────────────────────────────────

def ema(series: pd.Series, length: int) -> pd.Series:
    """
    Exponential Moving Average.
    
    Args:
        series: Price series
        length: EMA length
    
    Returns:
        EMA series
    """
    return series.ewm(span=length, adjust=False).mean()


def sma(series: pd.Series, length: int) -> pd.Series:
    """
    Simple Moving Average.
    
    Args:
        series: Price series
        length: SMA length
    
    Returns:
        SMA series
    """
    return series.rolling(window=length).mean()


# ─────────────────────────────────────────────────────────────────────
# Momentum Indicators
# ─────────────────────────────────────────────────────────────────────

def rsi(series: pd.Series, length: int = 14) -> pd.Series:
    """
    Relative Strength Index.
    
    Args:
        series: Price series (usually close)
        length: RSI period (default 14)
    
    Returns:
        RSI series (0-100)
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=length - 1, adjust=False).mean()
    avg_loss = loss.ewm(com=length - 1, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal_len: int = 9) \
        -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD (Moving Average Convergence Divergence).
    
    Args:
        close: Close price series
        fast: Fast EMA length (default 12)
        slow: Slow EMA length (default 26)
        signal_len: Signal line EMA length (default 9)
    
    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal_len)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


# ─────────────────────────────────────────────────────────────────────
# Volatility Indicators
# ─────────────────────────────────────────────────────────────────────

def atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    """
    Average True Range.
    
    Measures volatility using true range (max of: H-L, |H-PC|, |L-PC|).
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        length: ATR period (default 14)
    
    Returns:
        ATR series
    """
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(com=length - 1, adjust=False).mean()


def bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0) \
                   -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands.
    
    Args:
        close: Close price series
        period: BB period (default 20)
        std_dev: Standard deviations (default 2.0)
    
    Returns:
        Tuple of (Upper band, Middle (SMA), Lower band)
    """
    middle = sma(close, period)
    std = close.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return upper, middle, lower


# ─────────────────────────────────────────────────────────────────────
# Trend Indicators
# ─────────────────────────────────────────────────────────────────────

def supertrend(high: pd.Series, low: pd.Series, close: pd.Series,
               factor: float = 3.0, atr_len: int = 10) -> pd.Series:
    """
    Supertrend indicator (matches Pine Script).
    
    Returns direction:
        -1 = bullish (price above supertrend line)
        +1 = bearish (price below supertrend line)
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        factor: ATR multiplier (default 3.0)
        atr_len: ATR period (default 10)
    
    Returns:
        Series of direction values (-1 or +1)
    """
    atr_vals = atr(high, low, close, atr_len)
    hl2 = (high + low) / 2.0
    
    # Raw bands
    raw_upper = hl2 + factor * atr_vals
    raw_lower = hl2 - factor * atr_vals
    
    n = len(close)
    upper = np.zeros(n)
    lower = np.zeros(n)
    st_dir = np.zeros(n)   # +1 bearish, -1 bullish
    
    close_arr = close.values
    upper_arr = raw_upper.values
    lower_arr = raw_lower.values
    
    # Initialize first bar
    upper[0] = upper_arr[0]
    lower[0] = lower_arr[0]
    st_dir[0] = 1  # Start bearish until proven otherwise
    
    for i in range(1, n):
        # Lower band (support in uptrend) — only tighten upward
        if lower_arr[i] > lower[i-1] or close_arr[i-1] < lower[i-1]:
            lower[i] = lower_arr[i]
        else:
            lower[i] = lower[i-1]
        
        # Upper band (resistance in downtrend) — only tighten downward
        if upper_arr[i] < upper[i-1] or close_arr[i-1] > upper[i-1]:
            upper[i] = upper_arr[i]
        else:
            upper[i] = upper[i-1]
        
        # Direction
        if st_dir[i-1] == 1:  # Previously bearish
            if close_arr[i] > upper[i]:
                st_dir[i] = -1  # Flip to bullish
            else:
                st_dir[i] = 1  # Stay bearish
        else:  # Previously bullish
            if close_arr[i] < lower[i]:
                st_dir[i] = 1  # Flip to bearish
            else:
                st_dir[i] = -1  # Stay bullish
    
    return pd.Series(st_dir, index=close.index, dtype=float)


# ─────────────────────────────────────────────────────────────────────
# Crossover Helpers
# ─────────────────────────────────────────────────────────────────────

def crossover(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """
    Detect crossover: series1 crosses above series2.
    
    Returns True where series1[i-1] <= series2[i-1] AND series1[i] > series2[i]
    """
    return (series1.shift(1) <= series2.shift(1)) & (series1 > series2)


def crossunder(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """
    Detect crossunder: series1 crosses below series2.
    
    Returns True where series1[i-1] >= series2[i-1] AND series1[i] < series2[i]
    """
    return (series1.shift(1) >= series2.shift(1)) & (series1 < series2)


# ─────────────────────────────────────────────────────────────────────
# Batch Indicator Application
# ─────────────────────────────────────────────────────────────────────

def apply_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all technical indicators to a OHLCV DataFrame.
    
    Added columns:
        - ema_9, ema_21, ema_50, ema_200
        - rsi_14
        - atr_14
        - bb_upper, bb_middle, bb_lower
        - macd, macd_signal, macd_hist
        - supertrend
        - crossover_9_21, crossunder_9_21
    
    Args:
        df: DataFrame with OHLCV columns
    
    Returns:
        DataFrame with indicators added and NaN rows dropped
    """
    df = df.copy()
    
    # Flatten MultiIndex columns if yfinance returns them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Ensure required columns exist
    required = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    c = df['Close']
    h = df['High']
    l = df['Low']
    
    # Moving Averages
    df['ema_9'] = ema(c, 9)
    df['ema_21'] = ema(c, 21)
    df['ema_50'] = ema(c, 50)
    df['ema_200'] = ema(c, 200)
    
    # Momentum
    df['rsi_14'] = rsi(c, 14)
    df['macd'], df['macd_signal'], df['macd_hist'] = macd(c, 12, 26, 9)
    
    # Volatility
    df['atr_14'] = atr(h, l, c, 14)
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = bollinger_bands(c, 20, 2.0)
    
    # Trend
    df['supertrend'] = supertrend(h, l, c, 3.0, 10)
    
    # Crossovers
    df['crossover_9_21'] = crossover(df['ema_9'], df['ema_21'])
    df['crossunder_9_21'] = crossunder(df['ema_9'], df['ema_21'])
    
    # Drop NaN rows from indicator calculation
    df.dropna(inplace=True)
    
    return df
