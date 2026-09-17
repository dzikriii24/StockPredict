"""
indicators.py — Technical Analysis Indicators

Calculates: MA, RSI, MACD, Bollinger Bands, Volume metrics,
Support & Resistance levels.
"""

import pandas as pd
import numpy as np
from typing import Tuple


def add_moving_averages(df: pd.DataFrame, periods: list = [20, 50]) -> pd.DataFrame:
    """
    Add Simple Moving Averages.

    Args:
        df: DataFrame with 'Close' column
        periods: List of MA periods (default: [20, 50])

    Returns:
        DataFrame with MA columns added
    """
    df = df.copy()
    for period in periods:
        df[f"MA{period}"] = df["Close"].rolling(window=period).mean()
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate Relative Strength Index (RSI).

    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss over 'period' days

    Args:
        df: DataFrame with 'Close' column
        period: RSI period (default: 14)

    Returns:
        DataFrame with 'RSI' column added
    """
    df = df.copy()
    delta = df["Close"].diff()

    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    # Use exponential moving average for smoother RSI
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    return df


def add_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> pd.DataFrame:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    MACD Line = EMA(fast) - EMA(slow)
    Signal Line = EMA(MACD, signal)
    Histogram = MACD - Signal

    Args:
        df: DataFrame with 'Close' column
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal EMA period (default: 9)

    Returns:
        DataFrame with MACD, MACD_Signal, MACD_Hist columns
    """
    df = df.copy()

    ema_fast = df["Close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["Close"].ewm(span=slow, adjust=False).mean()

    df["MACD"] = ema_fast - ema_slow
    df["MACD_Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    return df


def add_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0
) -> pd.DataFrame:
    """
    Calculate Bollinger Bands.

    Middle Band = SMA(period)
    Upper Band = Middle + std_dev * StdDev
    Lower Band = Middle - std_dev * StdDev

    Args:
        df: DataFrame with 'Close' column
        period: SMA period (default: 20)
        std_dev: Standard deviation multiplier (default: 2.0)

    Returns:
        DataFrame with BB_Upper, BB_Middle, BB_Lower columns
    """
    df = df.copy()

    df["BB_Middle"] = df["Close"].rolling(window=period).mean()
    rolling_std = df["Close"].rolling(window=period).std()

    df["BB_Upper"] = df["BB_Middle"] + (std_dev * rolling_std)
    df["BB_Lower"] = df["BB_Middle"] - (std_dev * rolling_std)

    return df


def add_volume_indicators(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """
    Add volume-based indicators.

    - Volume_MA20: 20-day moving average of volume
    - Volume_Ratio: Current volume / Volume_MA20

    Args:
        df: DataFrame with 'Volume' column
        period: MA period for volume (default: 20)

    Returns:
        DataFrame with volume indicator columns
    """
    df = df.copy()

    if "Volume" in df.columns:
        df["Volume_MA20"] = df["Volume"].rolling(window=period).mean()
        # Handle 0/0 division safely (fill with 1.0)
        df["Volume_Ratio"] = df["Volume"].div(df["Volume_MA20"]).fillna(1.0)
        # If Volume is exactly 0 everywhere (like some indices), replace inf with 1.0
        df["Volume_Ratio"] = df["Volume_Ratio"].replace([np.inf, -np.inf], 1.0)
    else:
        df["Volume_MA20"] = 0
        df["Volume_Ratio"] = 1.0

    return df


def add_support_resistance(
    df: pd.DataFrame,
    window: int = 20
) -> pd.DataFrame:
    """
    Calculate simple support and resistance levels
    based on rolling high/low.

    Args:
        df: DataFrame with 'High' and 'Low' columns
        window: Rolling window for support/resistance (default: 20)

    Returns:
        DataFrame with Support and Resistance columns
    """
    df = df.copy()

    df["Resistance"] = df["High"].rolling(window=window).max()
    df["Support"] = df["Low"].rolling(window=window).min()

    return df


def add_ema(df: pd.DataFrame, periods: list = [9, 20, 50]) -> pd.DataFrame:
    """Add Exponential Moving Averages."""
    df = df.copy()
    for period in periods:
        df[f"EMA{period}"] = df["Close"].ewm(span=period, adjust=False).mean()
    return df


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate Average True Range (ATR)."""
    df = df.copy()
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["ATR"] = true_range.rolling(window=period).mean()
    return df


def add_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate Average Directional Index (ADX) — trend strength."""
    df = df.copy()
    plus_dm = df["High"].diff()
    minus_dm = -df["Low"].diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    atr = df.get("ATR")
    if atr is None or atr.isna().all():
        high_low = df["High"] - df["Low"]
        high_close = (df["High"] - df["Close"].shift()).abs()
        low_close = (df["Low"] - df["Close"].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

    plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, 1)) * 100
    df["ADX"] = dx.ewm(span=period, adjust=False).mean()
    df["Plus_DI"] = plus_di
    df["Minus_DI"] = minus_di
    return df


def add_roc(df: pd.DataFrame, period: int = 10) -> pd.DataFrame:
    """Calculate Rate of Change (ROC)."""
    df = df.copy()
    df["ROC"] = ((df["Close"] - df["Close"].shift(period)) / df["Close"].shift(period)) * 100
    return df


def add_stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> pd.DataFrame:
    """Calculate Stochastic Oscillator (%K and %D)."""
    df = df.copy()
    low_min = df["Low"].rolling(window=k_period).min()
    high_max = df["High"].rolling(window=k_period).max()
    df["Stoch_K"] = ((df["Close"] - low_min) / (high_max - low_min).replace(0, 1)) * 100
    df["Stoch_D"] = df["Stoch_K"].rolling(window=d_period).mean()
    return df


def add_vwap(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate VWAP (Volume Weighted Average Price). Best for intraday data."""
    df = df.copy()
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    cum_vol = df["Volume"].cumsum()
    cum_tp_vol = (typical_price * df["Volume"]).cumsum()
    df["VWAP"] = cum_tp_vol / cum_vol.replace(0, 1)
    return df


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all technical indicators to the DataFrame.

    This is the main entry point for adding all indicators at once.

    Args:
        df: Preprocessed DataFrame with OHLCV + features

    Returns:
        DataFrame with all technical indicator columns
    """
    df = add_moving_averages(df)
    df = add_ema(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_bollinger_bands(df)
    df = add_volume_indicators(df)
    df = add_support_resistance(df)
    df = add_atr(df)
    df = add_adx(df)
    df = add_roc(df)
    df = add_stochastic(df)
    df = add_vwap(df)

    return df


def get_indicator_explanations() -> dict:
    """
    Return explanations for each technical indicator.
    Used in the dashboard UI for tooltips and education.

    Returns:
        Dictionary with indicator name -> explanation
    """
    return {
        "MA20 & MA50": (
            "Moving Average (MA) menghaluskan fluktuasi harga untuk melihat tren. "
            "MA20 (20 hari) menunjukkan tren jangka pendek, MA50 (50 hari) untuk jangka menengah. "
            "Jika MA20 > MA50 → tren bullish (Golden Cross). "
            "Jika MA20 < MA50 → tren bearish (Death Cross)."
        ),
        "RSI": (
            "Relative Strength Index (RSI) mengukur momentum harga pada skala 0-100. "
            "RSI > 70 → overbought (potensi koreksi turun). "
            "RSI < 30 → oversold (potensi rebound naik). "
            "RSI 30-70 → area netral."
        ),
        "MACD": (
            "MACD mengukur hubungan antara dua EMA. "
            "MACD Line = EMA(12) - EMA(26). "
            "Signal Line = EMA(9) dari MACD. "
            "Jika MACD > Signal → momentum bullish. "
            "Jika MACD < Signal → momentum bearish."
        ),
        "Bollinger Bands": (
            "Bollinger Bands menunjukkan volatilitas harga. "
            "Upper Band = SMA20 + 2×StdDev. "
            "Lower Band = SMA20 - 2×StdDev. "
            "Harga mendekati Upper Band → potensi overbought. "
            "Harga mendekati Lower Band → potensi oversold."
        ),
        "Volume": (
            "Volume menunjukkan jumlah saham yang diperdagangkan. "
            "Volume Ratio > 1 → volume di atas rata-rata (minat tinggi). "
            "Volume Ratio < 1 → volume di bawah rata-rata."
        ),
        "Support & Resistance": (
            "Support adalah level harga di mana permintaan cenderung kuat (harga sulit turun lebih jauh). "
            "Resistance adalah level di mana penawaran cenderung kuat (harga sulit naik lebih tinggi). "
            "Dihitung dari rolling low (support) dan rolling high (resistance) 20 hari."
        ),
    }
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Alias for add_all_indicators"""
    return add_all_indicators(df)

def get_technical_score(latest_row: pd.Series) -> int:
    """
    Calculate a technical score (0-5) based on latest indicators.
    """
    score = 0
    # Price vs MA20
    if latest_row.get("Close", 0) > latest_row.get("MA20", float('inf')):
        score += 1
    # MA20 vs MA50
    if latest_row.get("MA20", 0) > latest_row.get("MA50", float('inf')):
        score += 1
    # RSI
    rsi = latest_row.get("RSI", 50)
    if 30 <= rsi <= 70:
        if rsi > 50:
            score += 1
    elif rsi < 30: # oversold, potential buy
        score += 1
    # MACD
    if latest_row.get("MACD", 0) > latest_row.get("MACD_Signal", float('inf')):
        score += 1
    # Volume
    if latest_row.get("Volume_Ratio", 0) > 1.0:
        score += 1
        
    return min(score, 5)
