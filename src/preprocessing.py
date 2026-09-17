"""
preprocessing.py — Data Cleaning & Feature Engineering

Handles missing values, sorting, duplicate removal,
and creates derived features for analysis.
"""

import pandas as pd
import numpy as np
from typing import Optional


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw OHLCV data.

    Steps:
    1. Sort by date index
    2. Remove duplicate indices
    3. Forward-fill missing values
    4. Drop any remaining NaN rows
    5. Ensure numeric types

    Args:
        df: Raw OHLCV DataFrame with DatetimeIndex

    Returns:
        Cleaned DataFrame
    """
    df = df.copy()

    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # Sort by date
    df = df.sort_index()

    # Remove duplicate indices
    df = df[~df.index.duplicated(keep="first")]

    # Convert to numeric (handles any string values)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Forward-fill then drop remaining NaN
    df = df.ffill()
    df = df.dropna()

    # Remove rows with zero or negative prices (invalid data)
    price_cols = [c for c in ["Open", "High", "Low", "Close"] if c in df.columns]
    for col in price_cols:
        df = df[df[col] > 0]

    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived features to the dataset.

    Features added:
    - Daily_Return: percentage change of Close
    - HL_Pct: (High - Low) / Low * 100
    - CO_Pct: (Close - Open) / Open * 100
    - Volatility: 20-day rolling std of Daily_Return

    Args:
        df: Cleaned OHLCV DataFrame

    Returns:
        DataFrame with additional feature columns
    """
    df = df.copy()

    # Daily Return (percentage)
    df["Daily_Return"] = df["Close"].pct_change() * 100

    # High-Low Percentage
    df["HL_Pct"] = (df["High"] - df["Low"]) / df["Low"] * 100

    # Close-Open Percentage
    df["CO_Pct"] = (df["Close"] - df["Open"]) / df["Open"] * 100

    # Rolling Volatility (20-day standard deviation of daily returns)
    df["Volatility"] = df["Daily_Return"].rolling(window=20).std()

    return df


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Full preprocessing pipeline: clean + add features.

    Args:
        df: Raw OHLCV DataFrame

    Returns:
        Fully preprocessed DataFrame
    """
    df = clean_data(df)
    df = add_features(df)
    return df


def get_data_summary(df: pd.DataFrame) -> dict:
    """
    Generate a summary of the dataset.

    Args:
        df: Preprocessed DataFrame

    Returns:
        Dictionary with data summary statistics
    """
    summary = {
        "total_rows": len(df),
        "date_range": f"{df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}",
        "start_date": df.index.min(),
        "end_date": df.index.max(),
        "latest_close": df["Close"].iloc[-1] if "Close" in df.columns else None,
        "latest_volume": df["Volume"].iloc[-1] if "Volume" in df.columns else None,
        "avg_daily_return": df["Daily_Return"].mean() if "Daily_Return" in df.columns else None,
        "total_return_pct": ((df["Close"].iloc[-1] / df["Close"].iloc[0]) - 1) * 100 if "Close" in df.columns else None,
        "missing_values": df.isnull().sum().sum(),
    }
    return summary
