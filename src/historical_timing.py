import pandas as pd
import numpy as np
from datetime import datetime, time
import streamlit as st
import pytz

# ═══════════════════════════════════════════════════════════════════
# CACHING & DATA MANAGEMENT
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner=False)
def analyze_intraday_timing(ticker: str, df: pd.DataFrame, interval: str) -> dict:
    """
    Core function to calculate historical time-of-day performance.
    Segments intraday data by time windows and computes metrics.
    """
    is_intraday = interval in ["1m", "5m", "15m", "30m", "1h"]
    
    if df is None or df.empty or not is_intraday:
        return {
            "available": False,
            "reason": "Intraday data not available or timeframe is daily.",
            "windows": [],
            "summary": {}
        }
    
    # Ensure index is datetime and timezone aware (assume WIB or local market time)
    if not isinstance(df.index, pd.DatetimeIndex):
        return {"available": False, "reason": "Index is not datetime.", "windows": [], "summary": {}}
    
    # Extract time component (HH:MM)
    df_copy = df.copy()
    
    # Calculate returns (Close to Close)
    df_copy["Return"] = df_copy["Close"].pct_change() * 100
    
    # For OHLC returns (Open to Close for that specific candle)
    df_copy["Candle_Return"] = ((df_copy["Close"] - df_copy["Open"]) / df_copy["Open"]) * 100
    
    # Add time column
    df_copy["Time"] = df_copy.index.strftime("%H:%M")
    
    # Calculate Rolling RVOL baseline (e.g. 20 periods)
    df_copy["Avg_Vol_20"] = df_copy["Volume"].rolling(window=20, min_periods=5).mean()
    df_copy["RVOL"] = np.where(df_copy["Avg_Vol_20"] > 0, df_copy["Volume"] / df_copy["Avg_Vol_20"], 1.0)
    
    # Drop NAs
    df_copy = df_copy.dropna(subset=["Candle_Return"])
    
    # Group by Time
    grouped = df_copy.groupby("Time")
    
    windows = []
    total_days = len(np.unique(df_copy.index.date))
    
    for time_str, group in grouped:
        obs = len(group)
        # Yahoo Finance only provides up to 7 days for 1m data, meaning max 7 observations per specific minute.
        # So we must lower the threshold to allow 1m data to display.
        if obs < max(3, total_days * 0.4): # Minimum sample threshold
            continue
            
        win_rate = (len(group[group["Candle_Return"] > 0]) / obs) * 100
        avg_return = group["Candle_Return"].mean()
        median_return = group["Candle_Return"].median()
        avg_vol = group["Volume"].mean()
        avg_rvol = group["RVOL"].mean() if "RVOL" in group else 1.0
        
        # Volatility (Standard Deviation of returns)
        volatility = group["Candle_Return"].std()
        
        # Max Drawdown within the window (Low vs Open)
        group["Drawdown"] = ((group["Low"] - group["Open"]) / group["Open"]) * 100
        avg_drawdown = group["Drawdown"].mean()
        
        windows.append({
            "time": time_str,
            "observations": obs,
            "win_rate": round(win_rate, 1),
            "avg_return": round(avg_return, 3),
            "median_return": round(median_return, 3),
            "avg_volume": avg_vol,
            "rvol": round(avg_rvol, 2),
            "volatility": round(volatility, 3),
            "avg_drawdown": round(avg_drawdown, 3)
        })
        
    # Sort windows by time
    windows.sort(key=lambda x: x["time"])
    
    # Rank windows to find the "Historically Strong" ones
    # We rank based on a composite score: Win Rate + Median Return + RVOL - Drawdown
    for w in windows:
        # Normalize roughly
        wr_score = (w["win_rate"] - 50) / 10 # 50% = 0, 60% = 1
        ret_score = w["median_return"] * 2 # 0.5% = 1
        vol_score = (w["rvol"] - 1) * 0.5 # 3x = 1
        dd_score = abs(w["avg_drawdown"]) * 0.5 # Penalty
        w["score"] = wr_score + ret_score + vol_score - dd_score

    sorted_by_score = sorted(windows, key=lambda x: x["score"], reverse=True)
    
    # Determine top windows
    top_windows = sorted_by_score[:3] if len(sorted_by_score) >= 3 else sorted_by_score
    
    date_start = df.index.min().strftime("%Y-%m-%d")
    date_end = df.index.max().strftime("%Y-%m-%d")
    
    return {
        "available": True,
        "ticker": ticker,
        "interval": interval,
        "trading_days": total_days,
        "date_start": date_start,
        "date_end": date_end,
        "windows": windows,
        "top_windows": top_windows
    }

@st.cache_data(ttl=3600, show_spinner=False)
def generate_entry_exit_matrix(df: pd.DataFrame, interval: str) -> dict:
    """
    Computes a matrix showing historical median returns for entering at time X and exiting at time Y.
    """
    is_intraday = interval in ["1m", "5m", "15m", "30m", "1h"]
    if df is None or df.empty or not is_intraday:
        return {"available": False, "matrix": {}}
        
    df_copy = df.copy()
    df_copy["Date"] = df_copy.index.date
    df_copy["Time"] = df_copy.index.strftime("%H:%M")
    
    # We need to map Date -> {Time: Close Price}
    pivot = df_copy.pivot(index="Date", columns="Time", values="Close")
    times = sorted(pivot.columns)
    
    matrix = {}
    
    for entry_time in times:
        matrix[entry_time] = {}
        for exit_time in times:
            if exit_time <= entry_time:
                matrix[entry_time][exit_time] = None
                continue
                
            # Calculate return from entry to exit for all available dates
            entry_prices = pivot[entry_time]
            exit_prices = pivot[exit_time]
            
            # Drop NAs where we don't have both entry and exit on that date
            valid = pd.concat([entry_prices, exit_prices], axis=1).dropna()
            if valid.empty or len(valid) < 3:
                matrix[entry_time][exit_time] = None
                continue
                
            returns = ((valid[exit_time] - valid[entry_time]) / valid[entry_time]) * 100
            
            matrix[entry_time][exit_time] = {
                "median_return": round(returns.median(), 3),
                "win_rate": round((len(returns[returns > 0]) / len(returns)) * 100, 1),
                "observations": len(returns)
            }
            
    return {
        "available": True,
        "times": times,
        "matrix": matrix
    }

def evaluate_current_context(current_time_str: str, current_rvol: float, current_momentum: str, historical_profile: dict) -> dict:
    """
    Compares the current market condition to the historical profile for this time window.
    """
    if not historical_profile.get("available") or not historical_profile.get("windows"):
        return {"status": "NO_DATA", "message": "Data historis intraday tidak tersedia."}
        
    windows = historical_profile["windows"]
    
    # Find the nearest window
    current_window = None
    for w in windows:
        if w["time"] <= current_time_str:
            current_window = w
            
    if not current_window:
        current_window = windows[0]
        
    # Check if it's a top window
    is_top = any(tw["time"] == current_window["time"] for tw in historical_profile.get("top_windows", []))
    
    # Volume comparison
    vol_status = "NORMAL"
    if current_rvol > current_window["rvol"] * 1.5:
        vol_status = "TINGGI"
    elif current_rvol < current_window["rvol"] * 0.5:
        vol_status = "RENDAH"
        
    message = f"Waktu saat ini ({current_time_str}) memiliki baseline Win Rate historis {current_window['win_rate']}%."
    if is_top:
        message = f"🔥 Saat ini berada di dalam historically active window ({current_window['time']})."
        
    return {
        "current_window": current_window["time"],
        "is_top_window": is_top,
        "volume_vs_history": vol_status,
        "message": message,
        "historical_win_rate": current_window['win_rate'],
        "historical_median_return": current_window['median_return']
    }

@st.cache_data(ttl=3600, show_spinner=False)
def analyze_opening_range(df: pd.DataFrame, interval: str) -> dict:
    """
    Opening Range Breakout (ORB) statistics.
    """
    is_intraday = interval in ["1m", "5m", "15m", "30m", "1h"]
    if df is None or df.empty or not is_intraday:
        return {"available": False}
        
    df_copy = df.copy()
    df_copy["Date"] = df_copy.index.date
    df_copy["Time"] = df_copy.index.strftime("%H:%M")
    
    # For Indonesian market, open is typically 09:00
    # Let's find the first candle of each day
    daily_groups = df_copy.groupby("Date")
    
    orb_stats = {
        "First_15m": {"breakout_up": 0, "breakout_down": 0, "total": 0, "avg_cont_up": 0, "avg_cont_down": 0}
    }
    
    # A simplified ORB calculation
    for date, group in daily_groups:
        if len(group) < 5:
            continue
            
        if interval == "1m":
            n_bars = 15
        elif interval == "5m":
            n_bars = 3
        elif interval == "15m":
            n_bars = 1
        else:
            n_bars = 1
            
        first_15m = group.iloc[:n_bars]
        rest_of_day = group.iloc[n_bars:]
        
        if rest_of_day.empty:
            continue
            
        orb_high = first_15m["High"].max()
        orb_low = first_15m["Low"].min()
        max_rest = rest_of_day["High"].max()
        min_rest = rest_of_day["Low"].min()
        
        orb_stats["First_15m"]["total"] += 1
        
        if max_rest > orb_high:
            orb_stats["First_15m"]["breakout_up"] += 1
            max_cont = ((max_rest - orb_high) / orb_high) * 100
            orb_stats["First_15m"]["avg_cont_up"] += max_cont
            
        if min_rest < orb_low:
            orb_stats["First_15m"]["breakout_down"] += 1
            max_drop = ((orb_low - min_rest) / orb_low) * 100
            orb_stats["First_15m"]["avg_cont_down"] += max_drop

    total = orb_stats["First_15m"]["total"]
    if total > 0:
        if orb_stats["First_15m"]["breakout_up"] > 0:
            orb_stats["First_15m"]["avg_cont_up"] /= orb_stats["First_15m"]["breakout_up"]
        if orb_stats["First_15m"]["breakout_down"] > 0:
            orb_stats["First_15m"]["avg_cont_down"] /= orb_stats["First_15m"]["breakout_down"]
    
    return {
        "available": True,
        "message": "Analisis Pergerakan Awal Sesi selesai.",
        "stats": orb_stats
    }
