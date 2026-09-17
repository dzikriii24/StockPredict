"""
macro_data.py — Macroeconomic & Market Data Module

Fetches macro/market indicators via yfinance:
- IHSG (^JKSE)
- USD/IDR (USDIDR=X)
- Gold (GC=F)
- Oil WTI (CL=F)

Calculates market context features:
- Daily returns for each indicator
- Market volatility
- Relative strength (stock vs IHSG)
"""

import pandas as pd
import numpy as np
import yfinance as yf
from typing import Optional, Dict
from datetime import datetime, timedelta


# Macro indicator tickers
MACRO_TICKERS = {
    "IHSG": "^JKSE",
    "USD_IDR": "USDIDR=X",
    "Gold": "GC=F",
    "Oil": "CL=F",
}


def fetch_macro_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Fetch all macro indicator data from Yahoo Finance.

    Args:
        start_date: Start date (YYYY-MM-DD), default 3 years ago
        end_date: End date (YYYY-MM-DD), default today

    Returns:
        Dictionary mapping indicator name -> DataFrame
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=3*365)).strftime("%Y-%m-%d")

    results = {}

    for name, ticker in MACRO_TICKERS.items():
        try:
            data = yf.Ticker(ticker).history(start=start_date, end=end_date)
            if data is not None and not data.empty:
                # Handle MultiIndex
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                # Keep only Close
                if "Close" in data.columns:
                    df = data[["Close"]].copy()
                    df.columns = [name]
                    df = df.dropna()
                    results[name] = df
        except Exception as e:
            print(f"⚠️ Could not fetch {name} ({ticker}): {e}")

    return results


def build_macro_features(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Build macro feature DataFrame with all indicators and their returns.

    Features:
    - IHSG, USD_IDR, Gold, Oil (close prices)
    - IHSG_Return, USDIDR_Return, Gold_Return, Oil_Return (daily %)
    - Market_Volatility (IHSG 20-day rolling std)

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        DataFrame with all macro features indexed by date
    """
    macro_data = fetch_macro_data(start_date, end_date)

    if not macro_data:
        return pd.DataFrame()

    # Combine all indicators
    combined = None
    for name, df in macro_data.items():
        if combined is None:
            combined = df
        else:
            combined = combined.join(df, how="outer")

    if combined is None or combined.empty:
        return pd.DataFrame()

    # Forward-fill missing dates (some indicators don't trade every day)
    combined = combined.sort_index()
    combined = combined.ffill()
    combined = combined.dropna()

    # Calculate daily returns
    for name in MACRO_TICKERS.keys():
        if name in combined.columns:
            combined[f"{name}_Return"] = combined[name].pct_change() * 100

    # Market volatility (IHSG 20-day rolling std of returns)
    if "IHSG_Return" in combined.columns:
        combined["Market_Volatility"] = combined["IHSG_Return"].rolling(window=20).std()

    return combined


def merge_macro_with_stock(
    stock_df: pd.DataFrame,
    macro_df: pd.DataFrame,
    ticker: str = None
) -> pd.DataFrame:
    """
    Merge macro features into stock DataFrame.
    Calculates relative strength (stock return vs IHSG return).

    No future data leakage: macro data is matched by date.

    Args:
        stock_df: Stock DataFrame with DatetimeIndex
        macro_df: Macro features DataFrame
        ticker: Stock ticker (for logging)

    Returns:
        Stock DataFrame with macro columns added
    """
    if macro_df.empty:
        # Add empty macro columns
        for col in ["IHSG_Return", "USDIDR_Return", "Gold_Return",
                     "Oil_Return", "Market_Volatility", "Relative_Strength"]:
            stock_df[col] = 0.0
        return stock_df

    df = stock_df.copy()

    # Select feature columns
    feature_cols = [c for c in macro_df.columns if "_Return" in c or c == "Market_Volatility"]

    if not feature_cols:
        for col in ["IHSG_Return", "USDIDR_Return", "Gold_Return",
                     "Oil_Return", "Market_Volatility", "Relative_Strength"]:
            df[col] = 0.0
        return df

    # Reindex macro to stock dates and forward-fill
    macro_aligned = macro_df[feature_cols].reindex(df.index, method="ffill")

    # Merge
    for col in feature_cols:
        df[col] = macro_aligned[col].fillna(0)

    # Calculate Relative Strength = Stock Return - IHSG Return
    if "Daily_Return" in df.columns and "IHSG_Return" in df.columns:
        df["Relative_Strength"] = df["Daily_Return"] - df["IHSG_Return"]
    else:
        df["Relative_Strength"] = 0.0

    return df


def get_macro_summary(macro_df: pd.DataFrame) -> dict:
    """
    Get summary of latest macro indicators.

    Args:
        macro_df: Macro features DataFrame

    Returns:
        Dictionary with latest values and changes
    """
    if macro_df.empty:
        return {}

    latest = macro_df.iloc[-1]
    summary = {}

    for name in MACRO_TICKERS.keys():
        if name in macro_df.columns:
            current = latest[name]
            ret_col = f"{name}_Return"
            daily_change = latest.get(ret_col, 0)

            summary[name] = {
                "value": round(current, 2),
                "daily_change": round(daily_change, 2),
                "label": _get_macro_label(name),
            }

    # Market trend
    if "IHSG_Return" in macro_df.columns:
        ihsg_returns = macro_df["IHSG_Return"].dropna()
        if len(ihsg_returns) >= 5:
            recent_avg = ihsg_returns.tail(5).mean()
            if recent_avg > 0.1:
                summary["market_trend"] = "🟢 Positive"
            elif recent_avg < -0.1:
                summary["market_trend"] = "🔴 Negative"
            else:
                summary["market_trend"] = "🟡 Neutral"
        else:
            summary["market_trend"] = "🟡 Neutral"

    if "Market_Volatility" in macro_df.columns:
        vol = latest.get("Market_Volatility", 0)
        summary["market_volatility"] = round(vol, 2)

    return summary


def _get_macro_label(name: str) -> str:
    """Get display label for macro indicator."""
    labels = {
        "IHSG": "IHSG (Jakarta Composite)",
        "USD_IDR": "USD/IDR Exchange Rate",
        "Gold": "Gold (USD/oz)",
        "Oil": "Oil WTI (USD/bbl)",
    }
    return labels.get(name, name)


def get_macro_chart_data(macro_df: pd.DataFrame) -> dict:
    """
    Prepare data for macro charts.

    Args:
        macro_df: Macro features DataFrame

    Returns:
        Dictionary with chart-ready data for each indicator
    """
    if macro_df.empty:
        return {}

    chart_data = {}
    for name in MACRO_TICKERS.keys():
        if name in macro_df.columns:
            chart_data[name] = {
                "dates": macro_df.index,
                "values": macro_df[name],
                "returns": macro_df.get(f"{name}_Return", pd.Series(dtype=float)),
                "label": _get_macro_label(name),
            }

    return chart_data
