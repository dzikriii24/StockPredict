"""
short_term_scanner.py — Serious Short-Term / Scalping Market Scanner Engine ⚡

Professional-grade screening system for Indonesian stocks.
Identifies stocks with strong short-term trading setups (intraday to 5 days).

Pipeline: ALL STOCKS → FAST SCREEN → TOP N → DEEP ANALYSIS → SCORED & RANKED

DISCLAIMER: This is an analytical ranking tool, NOT financial advice.
No prediction is a guarantee. No score ensures profit.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from typing import List, Dict, Any, Optional, Tuple

from src.company_metadata import metadata_manager
from src.data_loader import fetch_stock_data
from src.indicators import calculate_indicators
from src.prediction import train_and_predict
from src.news_loader import get_contextual_news
from src.sentiment import analyze_news_dataframe
from src.trading_strategy import generate_technical_signals_series
from src.backtesting import run_backtest
from src.historical_timing import analyze_intraday_timing, evaluate_current_context


# ═══════════════════════════════════════════════════════════════════
# 1. BEGINNER-FRIENDLY EXPLANATIONS (TOOLTIPS)
# ═══════════════════════════════════════════════════════════════════
METRIC_TOOLTIPS = {
    "RVOL": "Seberapa ramai saham ini ditransaksikan sekarang dibanding biasanya.",
    "VWAP": "Rata-rata harga transaksi (sering dianggap sebagai patokan harga wajar hari ini).",
    "Support": "Lantai harga. Biasanya harga susah turun lebih jauh dari titik ini.",
    "Resistance": "Atap harga. Biasanya harga susah naik lebih tinggi dari titik ini.",
    "ATR": "Seberapa lincah saham ini bergerak naik-turun tiap harinya.",
    "Risk/Reward": "Berapa banyak potensi untung dibanding potensi ruginya.",
    "Entry Zone": "Area harga yang pas untuk mulai beli.",
    "RSI": "Apakah saham ini sudah terlalu banyak yang beli (kemahalan) atau terlalu banyak yang jual (murah).",
    "MACD": "Melihat apakah arah pergerakan harga sedang mau naik atau malah mau turun.",
    "Volume": "Total lembar saham yang ditransaksikan.",
    "ADX": "Seberapa kuat arah pergerakan harga yang sedang terjadi sekarang.",
    "ROC": "Seberapa cepat harga berubah.",
    "Stochastic": "Mirip RSI, melihat apakah harga sedang di pucuk atau di dasar.",
    "EMA": "Garis tren harga jangka pendek.",
    "Breakout": "Harga berhasil menjebol atap (Resistance) dan biasanya akan lanjut naik.",
    "Pullback": "Harga turun sementara untuk ambil napas sebelum lanjut naik lagi.",
    "Stop Loss": "Batas harga untuk jual rugi supaya kerugian tidak semakin dalam.",
}


# ═══════════════════════════════════════════════════════════════════
# 2. FAST SCANNER (TRADEABILITY FILTER)
# ═══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=900, show_spinner=False)
def fast_scan_universe(interval: str = "1d") -> List[Dict]:
    """
    Phase 1: Lightweight scan to filter by tradeability.
    Returns list of dicts with basic price/volume data + raw DataFrame.
    """
    tickers = metadata_manager.get_all_tickers()
    end_date = datetime.now()

    lookback = {"1m": 6, "5m": 14, "15m": 59, "30m": 59, "1h": 90, "1d": 180}
    days = lookback.get(interval, 180)
    start_date = end_date - timedelta(days=days)

    results = []
    for ticker in tickers:
        try:
            df = fetch_stock_data(
                ticker,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                interval=interval,
            )
            if df.empty or len(df) < 20:
                continue

            latest = df.iloc[-1]
            prev = df.iloc[-2]
            price = latest.get("Close", 0)
            vol = latest.get("Volume", 0)
            avg_vol_20 = df["Volume"].tail(20).mean()
            avg_vol_5 = df["Volume"].tail(5).mean()

            # Tradeability filter
            if price < 50 or vol == 0 or avg_vol_20 < 5000:
                continue

            pct_change = ((price - prev["Close"]) / prev["Close"]) * 100
            rvol = vol / avg_vol_20 if avg_vol_20 > 0 else 1.0
            trading_value = price * vol

            # Volume trend (5-day vs 20-day)
            vol_trend = avg_vol_5 / avg_vol_20 if avg_vol_20 > 0 else 1.0

            # Volume consistency (std / mean — lower is more consistent)
            vol_std = df["Volume"].tail(20).std()
            vol_consistency = 1.0 - min(vol_std / avg_vol_20, 1.0) if avg_vol_20 > 0 else 0.5

            # Tradeability score (0-100)
            trade_vol = min(avg_vol_20 / 1_000_000, 1.0) * 25  # Volume score
            trade_liq = min(trading_value / 5_000_000_000, 1.0) * 25  # Liquidity score
            trade_act = min(rvol / 2.0, 1.0) * 25  # Activity score
            trade_dq = min(len(df) / 100, 1.0) * 25  # Data quality
            tradeability = trade_vol + trade_liq + trade_act + trade_dq

            results.append({
                "Ticker": ticker,
                "Price": price,
                "Open": latest.get("Open", price),
                "High": latest.get("High", price),
                "Low": latest.get("Low", price),
                "Prev_Close": prev["Close"],
                "Change_Pct": round(pct_change, 2),
                "Volume": vol,
                "Avg_Volume": avg_vol_20,
                "RVOL": round(rvol, 2),
                "Trading_Value": trading_value,
                "Vol_Trend": round(vol_trend, 2),
                "Vol_Consistency": round(vol_consistency, 2),
                "Tradeability": round(tradeability, 1),
                "df": df,
            })
        except Exception:
            continue

    if not results:
        return []

    # Sort by tradeability + momentum proxy
    results.sort(key=lambda x: x["Tradeability"] * (1 + abs(x["Change_Pct"]) / 10), reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════
# 3. DEEP ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800, show_spinner=False)
def run_deep_analysis(
    fast_results: list,
    top_n: int = 15,
    interval: str = "1d",
    mode: str = "5d",
) -> List[Dict]:
    """
    Phase 2: Heavy analysis on top N stocks.
    Runs full technicals, ML, news, and all sub-engines.
    """
    analyzed = []
    candidates = fast_results[:top_n]

    for cand in candidates:
        ticker = cand["Ticker"]
        df_raw = cand["df"]

        try:
            # ── Full technicals ──
            df_tech = calculate_indicators(df_raw)
            latest = df_tech.iloc[-1]

            # ── ML Prediction ──
            pred = train_and_predict(df_tech, ticker=f"{ticker}_{interval}_scanner")
            ml_data = _extract_ml_data(pred, mode)

            # ── News Catalyst ──
            news_data = _analyze_news(ticker)

            # ── Volume Analysis ──
            volume_analysis = analyze_volume(cand, df_tech)

            # ── Price Action ──
            price_action = analyze_price_action(df_tech)

            # ── Momentum ──
            momentum = analyze_momentum(latest)

            # ── VWAP (intraday only) ──
            vwap_data = analyze_vwap(latest, interval)

            # ── Support & Resistance ──
            sr_data = analyze_support_resistance(latest, df_tech)

            # ── Entry Zone ──
            entry = calculate_entry_zone(latest, sr_data, vwap_data, momentum, volume_analysis)

            # ── Take Profit ──
            tp = calculate_take_profit(latest["Close"], sr_data, latest.get("ATR", 0))

            # ── Stop Loss ──
            sl = calculate_stop_loss(latest["Close"], sr_data, latest.get("ATR", 0))

            # ── Risk/Reward ──
            rr = calculate_risk_reward(entry["preferred_entry"], tp, sl)

            # ── Entry Quality Score ──
            entry_score = calculate_entry_quality(
                sr_data, vwap_data, volume_analysis, momentum, rr, news_data
            )

            # ── Scalping Setup (intraday) ──
            scalping = detect_scalping_setup(
                latest, df_tech, vwap_data, sr_data, momentum, volume_analysis, interval
            )

            # ── Signal ──
            signal = generate_short_term_signal(
                momentum, volume_analysis, price_action, entry_score, cand["Change_Pct"]
            )

            # ── Historical Timing ──
            historical_timing = analyze_intraday_timing(ticker, df_raw, interval)
            # Assuming current time is WIB, but for testing we use datetime.now()
            # If market is closed, this might evaluate based on closing time, which is fine.
            current_time_str = datetime.now().strftime("%H:%M")
            if historical_timing.get("available"):
                timing_context = evaluate_current_context(
                    current_time_str, volume_analysis["rvol"], momentum["strength"], historical_timing
                )
                historical_timing["context"] = timing_context
            else:
                historical_timing["context"] = {"status": "NO_DATA", "message": "Data historis tidak mencukupi untuk timeframe ini."}

            # ── Backtesting (Historical Performance) ──
            try:
                df_signals = generate_technical_signals_series(df_tech)
                # target and SL using dynamic ATR logic simplified to percentages
                avg_atr_pct = (latest.get("ATR", 100) / latest.get("Close", 1)) * 100
                bt_results = run_backtest(df_signals, initial_capital=10_000_000, target_pct=max(avg_atr_pct*1.5, 2.0), stop_loss_pct=max(avg_atr_pct, 1.0))
                backtest_metrics = bt_results["metrics"]
            except Exception as e:
                backtest_metrics = {"win_rate": 0, "total_return": 0, "max_drawdown": 0, "num_trades": 0}

            # ── Sector Context ──
            sector_ctx = {"relative_strength": "N/A"}  # Populated later in batch

            # ── High Risk Detection ──
            high_risk, risk_reasons = detect_high_risk(
                latest, cand["RVOL"], cand["Change_Pct"], volume_analysis
            )

            # ── Final Opportunity Score ──
            opp_score = calculate_opportunity_score(
                tradeability=cand["Tradeability"],
                volume_score=volume_analysis["score"],
                momentum_score=momentum["score"],
                entry_score=entry_score["score"],
                rr_score=min(rr["ratio"] * 20, 20) if rr["ratio"] > 0 else 0,
                news_score=news_data["score"],
                ml_score=ml_data["score"],
                is_overextended=(cand["Change_Pct"] > 8),
                is_high_risk=high_risk,
            )

            meta = metadata_manager.get_metadata(ticker)

            analyzed.append({
                "Ticker": ticker,
                "Company": meta["company"],
                "Sector": meta["sector"],
                "Price": cand["Price"],
                "Open": cand["Open"],
                "High": cand["High"],
                "Low": cand["Low"],
                "Prev_Close": cand["Prev_Close"],
                "Change_Pct": cand["Change_Pct"],
                "Volume": cand["Volume"],
                "Avg_Volume": cand["Avg_Volume"],
                "RVOL": cand["RVOL"],
                "Trading_Value": cand["Trading_Value"],
                "Tradeability": cand["Tradeability"],
                # Analysis results
                "Volume_Analysis": volume_analysis,
                "Price_Action": price_action,
                "Momentum": momentum,
                "VWAP": vwap_data,
                "Support_Resistance": sr_data,
                "Entry": entry,
                "Take_Profit": tp,
                "Stop_Loss": sl,
                "Risk_Reward": rr,
                "Entry_Score": entry_score,
                "df": df_raw,
                "Scalping": scalping,
                "Signal": signal,
                "Historical_Timing": historical_timing,
                "ML": ml_data,
                "News": news_data,
                "Sector_Context": sector_ctx,
                "High_Risk": high_risk,
                "Risk_Reasons": risk_reasons,
                "Score": opp_score,
                "Backtest": backtest_metrics,
            })

        except Exception as e:
            print(f"Scanner error on {ticker}: {e}")
            continue

    # Sort by final score
    analyzed.sort(key=lambda x: x["Score"], reverse=True)
    return analyzed


# ═══════════════════════════════════════════════════════════════════
# 4. SUB-ENGINES
# ═══════════════════════════════════════════════════════════════════

def _extract_ml_data(pred: dict, mode: str) -> dict:
    """Extract ML prediction data for the given horizon."""
    if not pred or pred.get("status") != "success":
        return {"prediction": "N/A", "probability": 0, "accuracy": 0, "score": 0,
                "d1": {}, "d3": {}, "d5": {}}

    horizons = pred.get("horizons", {})
    h_keys = list(horizons.keys())
    
    if len(h_keys) == 0:
        return {"prediction": "N/A", "probability": 0, "accuracy": 0, "score": 0,
                "d1": {}, "d3": {}, "d5": {}}
                
    d1 = horizons.get(h_keys[0], {})
    d5 = horizons.get(h_keys[len(h_keys)//2], {}) if len(h_keys) > 2 else d1
    d20 = horizons.get(h_keys[-1], {}) if len(h_keys) > 1 else d1

    # Use mode-appropriate horizon
    primary = d5 if mode in ["5d", "3d"] else d1
    ml_pred = primary.get("prediction", "N/A")
    ml_prob = primary.get("probability", 0)
    ml_acc = primary.get("accuracy", 0)

    score = 0
    if ml_pred == "UP" and ml_prob > 0.55:
        score = min(ml_prob * 10, 5)  # Max 5 pts

    return {
        "prediction": ml_pred, "probability": ml_prob, "accuracy": ml_acc,
        "score": score,
        "d1": d1, "d3": d5, "d5": d5, "d20": d20,
    }


def _analyze_news(ticker: str) -> dict:
    """Analyze news catalyst for a ticker."""
    try:
        news_df = get_contextual_news(ticker)
        if news_df.empty:
            return {"impact": "NO_DATA", "count": 0, "sentiment": 0, "score": 0, "strength": "NONE"}

        analyzed = analyze_news_dataframe(news_df, ticker)
        if analyzed.empty:
            return {"impact": "NEUTRAL", "count": len(news_df), "sentiment": 0, "score": 1, "strength": "LOW"}

        pos = len(analyzed[analyzed["impact"] == "POSITIVE"])
        neg = len(analyzed[analyzed["impact"] == "NEGATIVE"])
        total = len(analyzed)
        sentiment = (pos - neg) / total if total > 0 else 0

        if sentiment > 0.3:
            impact, score, strength = "POSITIVE", 5, "HIGH"
        elif sentiment > 0:
            impact, score, strength = "SLIGHT_POSITIVE", 3, "MEDIUM"
        elif sentiment < -0.3:
            impact, score, strength = "NEGATIVE", 0, "HIGH"
        else:
            impact, score, strength = "NEUTRAL", 1, "LOW"

        return {"impact": impact, "count": total, "sentiment": round(sentiment, 2),
                "score": score, "strength": strength}
    except Exception:
        return {"impact": "ERROR", "count": 0, "sentiment": 0, "score": 0, "strength": "NONE"}


# ── Volume Analysis ──
def analyze_volume(cand: dict, df_tech: pd.DataFrame) -> dict:
    """Comprehensive volume analysis."""
    vol = cand["Volume"]
    avg = cand["Avg_Volume"]
    rvol = cand["RVOL"]
    trading_val = cand["Trading_Value"]

    # Volume spike
    is_spike = rvol > 2.0
    spike_level = "EXTREME" if rvol > 4.0 else "HIGH" if rvol > 2.5 else "MODERATE" if rvol > 1.5 else "NORMAL"

    # Volume acceleration (today vs yesterday)
    if len(df_tech) >= 2:
        prev_vol = df_tech["Volume"].iloc[-2]
        vol_accel = vol / prev_vol if prev_vol > 0 else 1.0
    else:
        vol_accel = 1.0

    # Score (0-15 max for opportunity score)
    score = min(rvol * 5, 15)

    return {
        "current": vol, "average": avg, "rvol": rvol,
        "trading_value": trading_val,
        "spike": is_spike, "spike_level": spike_level,
        "acceleration": round(vol_accel, 2),
        "trend": cand["Vol_Trend"],
        "consistency": cand["Vol_Consistency"],
        "score": round(score, 1),
        "explanation": _explain_volume(rvol, spike_level, trading_val),
    }


def _explain_volume(rvol, spike_level, trading_val):
    val_str = f"Rp {trading_val/1e9:.1f}B" if trading_val > 1e9 else f"Rp {trading_val/1e6:.0f}M"
    if spike_level in ["EXTREME", "HIGH"]:
        return f"aktivitas transaksi hari ini sekitar {rvol:.1f}x rata-rata ({val_str}). ini SANGAT RAMAI."
    elif spike_level == "MODERATE":
        return f"aktivitas sedikit di atas rata-rata ({rvol:.1f}x, {val_str})."
    else:
        return f"aktivitas transaksi normal ({rvol:.1f}x rata-rata, {val_str})."


# ── Price Action ──
def analyze_price_action(df: pd.DataFrame) -> dict:
    """Analyze short-term price behavior."""
    if len(df) < 5:
        return {"condition": "INSUFFICIENT_DATA", "candle": {}, "patterns": []}

    latest = df.iloc[-1]
    body = abs(latest["Close"] - latest["Open"])
    upper_wick = latest["High"] - max(latest["Close"], latest["Open"])
    lower_wick = min(latest["Close"], latest["Open"]) - latest["Low"]
    total_range = latest["High"] - latest["Low"]

    # Detect conditions
    patterns = []
    condition = "NEUTRAL"

    # Breakout: Close > 20-period high (excluding today)
    if len(df) >= 21:
        recent_high = df["High"].iloc[-21:-1].max()
        recent_low = df["Low"].iloc[-21:-1].min()
        if latest["Close"] > recent_high:
            patterns.append("BREAKOUT")
            condition = "BREAKOUT"
        elif latest["Close"] < recent_low:
            patterns.append("BREAKDOWN")
            condition = "BREAKDOWN"

    # Pullback in uptrend
    ema20 = latest.get("EMA20", latest.get("MA20", 0))
    ema50 = latest.get("EMA50", latest.get("MA50", 0))
    if ema20 > ema50 and latest["Close"] < ema20 and latest["Close"] > ema50:
        patterns.append("PULLBACK")
        if condition == "NEUTRAL":
            condition = "PULLBACK"

    # Rebound from support
    support = latest.get("Support", 0)
    if support > 0 and latest["Low"] <= support * 1.01 and latest["Close"] > support:
        patterns.append("REBOUND")
        if condition == "NEUTRAL":
            condition = "REBOUND"

    # Consolidation (low ATR relative to price)
    atr = latest.get("ATR", 0)
    if atr > 0 and (atr / latest["Close"]) < 0.015:
        patterns.append("CONSOLIDATION")
        if condition == "NEUTRAL":
            condition = "CONSOLIDATION"

    # Trend continuation
    if ema20 > ema50 and latest["Close"] > ema20:
        patterns.append("TREND_UP")
        if condition == "NEUTRAL":
            condition = "TREND_CONTINUATION"

    return {
        "condition": condition,
        "patterns": patterns,
        "candle": {
            "body": round(body, 2),
            "upper_wick": round(upper_wick, 2),
            "lower_wick": round(lower_wick, 2),
            "range": round(total_range, 2),
            "bullish": latest["Close"] > latest["Open"],
        },
    }


# ── Momentum Engine ──
def analyze_momentum(latest: pd.Series) -> dict:
    """Multi-indicator momentum analysis."""
    rsi = latest.get("RSI", 50)
    macd = latest.get("MACD", 0)
    macd_sig = latest.get("MACD_Signal", 0)
    macd_hist = latest.get("MACD_Hist", 0)
    adx = latest.get("ADX", 20)
    roc = latest.get("ROC", 0)
    ema9 = latest.get("EMA9", 0)
    ema20 = latest.get("EMA20", latest.get("MA20", 0))
    ema50 = latest.get("EMA50", latest.get("MA50", 0))
    close = latest.get("Close", 0)

    # Strength assessment
    bullish_count = 0
    total_checks = 6

    if rsi > 50 and rsi < 75: bullish_count += 1
    if macd > macd_sig: bullish_count += 1
    if close > ema9: bullish_count += 1
    if close > ema20: bullish_count += 1
    if ema20 > ema50: bullish_count += 1
    if roc > 0: bullish_count += 1

    ratio = bullish_count / total_checks
    if ratio >= 0.8:
        strength = "STRONG"
    elif ratio >= 0.5:
        strength = "MODERATE"
    else:
        strength = "WEAK"

    # Trend direction
    if close > ema20 and ema20 > ema50:
        trend = "UP"
    elif close < ema20 and ema20 < ema50:
        trend = "DOWN"
    else:
        trend = "SIDEWAYS"

    # Score (0-15 for opportunity score)
    score = min(ratio * 15, 15)

    return {
        "strength": strength, "trend": trend,
        "rsi": round(rsi, 1), "macd": round(macd, 4),
        "macd_signal": round(macd_sig, 4),
        "macd_hist": round(macd_hist, 4),
        "adx": round(adx, 1), "roc": round(roc, 2),
        "ema9": round(ema9, 2), "ema20": round(ema20, 2), "ema50": round(ema50, 2),
        "bullish_signals": bullish_count, "total_signals": total_checks,
        "score": round(score, 1),
    }


# ── VWAP Analysis ──
def analyze_vwap(latest: pd.Series, interval: str) -> dict:
    """VWAP analysis. Only meaningful for intraday data."""
    vwap = latest.get("VWAP", 0)
    close = latest.get("Close", 0)
    is_intraday = interval in ["1m", "5m", "15m", "30m", "1h"]

    if vwap == 0 or not is_intraday:
        return {"available": False, "vwap": 0, "distance_pct": 0, "position": "N/A", "condition": "N/A"}

    distance = ((close - vwap) / vwap) * 100

    if close > vwap:
        position = "ABOVE"
        condition = "BULLISH"
    elif close < vwap:
        position = "BELOW"
        condition = "BEARISH"
    else:
        position = "AT"
        condition = "NEUTRAL"

    return {
        "available": True, "vwap": round(vwap, 2),
        "distance_pct": round(distance, 2),
        "position": position, "condition": condition,
    }


# ── Support & Resistance ──
def analyze_support_resistance(latest: pd.Series, df: pd.DataFrame) -> dict:
    """Find nearest support and resistance with distances."""
    support = latest.get("Support", 0)
    resistance = latest.get("Resistance", 0)
    close = latest.get("Close", 0)

    # Also compute swing high/low from last 10 bars
    if len(df) >= 10:
        swing_high = df["High"].iloc[-10:].max()
        swing_low = df["Low"].iloc[-10:].min()
    else:
        swing_high = resistance
        swing_low = support

    dist_support = ((close - support) / close) * 100 if support > 0 else 0
    dist_resistance = ((resistance - close) / close) * 100 if resistance > 0 else 0

    return {
        "support": round(support, 0),
        "resistance": round(resistance, 0),
        "swing_high": round(swing_high, 0),
        "swing_low": round(swing_low, 0),
        "dist_support_pct": round(dist_support, 2),
        "dist_resistance_pct": round(dist_resistance, 2),
    }


# ── Entry Zone Engine ──
def calculate_entry_zone(latest, sr, vwap, momentum, volume) -> dict:
    """Calculate preferred entry zone and alternative entry."""
    close = latest.get("Close", 0)
    atr = latest.get("ATR", close * 0.02)

    # Preferred entry: near support or VWAP, with buffer
    preferred_low = max(sr["support"], close - atr * 0.5)
    preferred_high = close

    # Reasons for this entry
    reasons = []
    if sr["dist_support_pct"] < 3.0:
        reasons.append("dekat area support")
    if vwap.get("available") and vwap["position"] == "ABOVE":
        reasons.append("harga di atas VWAP")
    if momentum["strength"] in ["STRONG", "MODERATE"]:
        reasons.append("momentum positif")
    if volume["rvol"] > 1.2:
        reasons.append("volume di atas rata-rata")

    # Alternative: breakout entry
    alt_entry = sr["resistance"]
    alt_confirmation = [
        "candle close di atas resistance",
        "volume > rata-rata",
        "momentum tetap positif",
    ]

    # Avoid entry if already overextended
    avoid = close > sr["resistance"] * 1.05
    avoid_reason = "harga sudah terlalu jauh di atas entry zone yang ideal" if avoid else ""

    return {
        "preferred_low": round(preferred_low, 0),
        "preferred_high": round(preferred_high, 0),
        "preferred_entry": round((preferred_low + preferred_high) / 2, 0),
        "reasons": reasons if reasons else ["setup teknikal stabil"],
        "alt_entry": round(alt_entry, 0),
        "alt_confirmation": alt_confirmation,
        "avoid": avoid,
        "avoid_reason": avoid_reason,
    }


# ── Take Profit Engine ──
def calculate_take_profit(close: float, sr: dict, atr: float) -> dict:
    """Structure-based take profit levels."""
    resistance = sr["resistance"]

    # TP1: nearest resistance
    tp1 = resistance if resistance > close else close + atr * 1.5
    tp1_pct = ((tp1 - close) / close) * 100

    # TP2: next resistance (swing high or ATR projection)
    tp2 = sr["swing_high"] if sr["swing_high"] > tp1 else tp1 + atr
    tp2_pct = ((tp2 - close) / close) * 100

    return {
        "tp1": round(tp1, 0), "tp1_pct": round(tp1_pct, 2),
        "tp2": round(tp2, 0), "tp2_pct": round(tp2_pct, 2),
    }


# ── Stop Loss Engine ──
def calculate_stop_loss(close: float, sr: dict, atr: float) -> dict:
    """Structure-based stop loss."""
    support = sr["support"]
    swing_low = sr["swing_low"]

    # Primary SL: below support
    sl_support = support - (atr * 0.3) if support > 0 else close - atr * 1.5

    # ATR-based SL
    sl_atr = close - atr * 1.5

    # Use whichever is tighter but still reasonable
    sl = max(sl_support, sl_atr)
    if sl >= close:
        sl = close - atr * 1.5

    sl_pct = ((close - sl) / close) * 100

    method = "di bawah area support" if sl == sl_support else "berdasarkan volatilitas (ATR)"

    return {
        "price": round(sl, 0),
        "loss_pct": round(sl_pct, 2),
        "method": method,
    }


# ── Risk/Reward Calculator ──
def calculate_risk_reward(entry: float, tp: dict, sl: dict) -> dict:
    """Calculate R/R ratio."""
    potential_profit = tp["tp1"] - entry
    potential_loss = entry - sl["price"]

    ratio = potential_profit / potential_loss if potential_loss > 0 else 0

    return {
        "entry": round(entry, 0),
        "tp1": tp["tp1"], "tp2": tp["tp2"],
        "sl": sl["price"],
        "profit_pct": tp["tp1_pct"],
        "loss_pct": sl["loss_pct"],
        "ratio": round(ratio, 2),
        "display": f"1 : {ratio:.1f}" if ratio > 0 else "N/A",
        "acceptable": ratio >= 1.5,
    }


# ── Entry Quality Score ──
def calculate_entry_quality(sr, vwap, volume, momentum, rr, news) -> dict:
    """Score 0-100 for entry quality."""
    score = 0
    components = {}

    # S/R proximity (15 pts)
    sr_pts = 15 if sr["dist_support_pct"] < 3 else 10 if sr["dist_support_pct"] < 5 else 5
    score += sr_pts
    components["Support/Resistance"] = sr_pts

    # VWAP (10 pts)
    vwap_pts = 10 if vwap.get("available") and vwap["position"] == "ABOVE" else 5 if vwap.get("available") else 3
    score += vwap_pts
    components["VWAP"] = vwap_pts

    # Volume (15 pts)
    vol_pts = min(volume["rvol"] * 5, 15)
    score += vol_pts
    components["Volume"] = round(vol_pts, 1)

    # Momentum (15 pts)
    mom_pts = 15 if momentum["strength"] == "STRONG" else 10 if momentum["strength"] == "MODERATE" else 3
    score += mom_pts
    components["Momentum"] = mom_pts

    # Trend (10 pts)
    trend_pts = 10 if momentum["trend"] == "UP" else 5 if momentum["trend"] == "SIDEWAYS" else 0
    score += trend_pts
    components["Trend"] = trend_pts

    # R/R (15 pts)
    rr_pts = 15 if rr["ratio"] >= 2.0 else 10 if rr["ratio"] >= 1.5 else 5 if rr["ratio"] >= 1.0 else 0
    score += rr_pts
    components["Risk/Reward"] = rr_pts

    # News (10 pts)
    news_pts = min(news["score"] * 2, 10)
    score += news_pts
    components["News"] = round(news_pts, 1)

    # Market (10 pts) — baseline
    market_pts = 5
    score += market_pts
    components["Market"] = market_pts

    return {"score": round(min(score, 100), 1), "components": components}


# ── Scalping Setup Detector ──
def detect_scalping_setup(latest, df, vwap, sr, momentum, volume, interval) -> dict:
    """Detect specific scalping setups for intraday data."""
    is_intraday = interval in ["1m", "5m", "15m", "30m", "1h"]
    if not is_intraday:
        return {"available": False, "setups": []}

    setups = []
    close = latest.get("Close", 0)

    # 1. VWAP Bounce
    if vwap.get("available") and vwap["position"] == "ABOVE" and abs(vwap["distance_pct"]) < 0.5:
        setups.append({
            "type": "VWAP_BOUNCE",
            "label": "VWAP Bounce",
            "entry": round(vwap["vwap"], 0),
            "sl": round(vwap["vwap"] - latest.get("ATR", 10) * 0.5, 0),
            "tp1": round(close + latest.get("ATR", 10), 0),
            "confirmation": "harga memantul dari VWAP dengan volume",
            "invalidation": "harga turun dan close di bawah VWAP",
        })

    # 2. Breakout + Volume
    if len(df) >= 21:
        recent_high = df["High"].iloc[-21:-1].max()
        if close > recent_high and volume["rvol"] > 1.5:
            setups.append({
                "type": "BREAKOUT_VOLUME",
                "label": "Breakout + Volume Confirmation",
                "entry": round(recent_high, 0),
                "sl": round(recent_high - latest.get("ATR", 10), 0),
                "tp1": round(close + latest.get("ATR", 10) * 1.5, 0),
                "confirmation": "candle close di atas resistance + volume tinggi",
                "invalidation": "harga kembali di bawah level breakout",
            })

    # 3. Support Bounce
    support = sr["support"]
    if support > 0 and close > support and (close - support) / close < 0.01:
        setups.append({
            "type": "SUPPORT_BOUNCE",
            "label": "Support Bounce",
            "entry": round(support, 0),
            "sl": round(support - latest.get("ATR", 10) * 0.5, 0),
            "tp1": round(close + latest.get("ATR", 10), 0),
            "confirmation": "harga memantul dari support dengan candle hijau",
            "invalidation": "harga break down di bawah support",
        })

    # 4. Momentum Continuation
    if momentum["strength"] == "STRONG" and volume["rvol"] > 1.3:
        setups.append({
            "type": "MOMENTUM_CONT",
            "label": "Momentum Continuation",
            "entry": round(close, 0),
            "sl": round(close - latest.get("ATR", 10) * 1.0, 0),
            "tp1": round(close + latest.get("ATR", 10) * 1.5, 0),
            "confirmation": "momentum tetap kuat + volume tinggi",
            "invalidation": "RSI divergence atau volume collapse",
        })

    return {"available": True, "setups": setups}


# ── Short-Term Signal ──
def generate_short_term_signal(momentum, volume, price_action, entry_score, change_pct) -> dict:
    """Generate signal: LONG_SETUP / WAIT / NO_TRADE / BREAKOUT_WATCH / PULLBACK_WATCH / HIGH_RISK."""
    score = entry_score["score"]
    condition = price_action["condition"]

    if score >= 75 and momentum["trend"] == "UP" and volume["rvol"] > 1.2:
        signal = "LONG_SETUP"
        color = "green"
    elif condition == "BREAKOUT":
        signal = "BREAKOUT_WATCH"
        color = "blue"
    elif condition == "PULLBACK" and momentum["trend"] == "UP":
        signal = "PULLBACK_WATCH"
        color = "orange"
    elif change_pct > 10 or change_pct < -8:
        signal = "HIGH_RISK"
        color = "red"
    elif score >= 50:
        signal = "WAIT"
        color = "gray"
    else:
        signal = "NO_TRADE"
        color = "gray"

    return {"signal": signal, "color": color}


# ── High Risk Detection ──
def detect_high_risk(latest, rvol, change_pct, volume) -> Tuple[bool, List[str]]:
    """Detect high-risk conditions."""
    reasons = []
    rsi = latest.get("RSI", 50)

    if rsi > 80:
        reasons.append("Overbought (RSI > 80). Rentan koreksi tajam.")
    if rvol > 5.0 and latest.get("Close", 0) < latest.get("Open", 0):
        reasons.append("Volume raksasa + candle merah (kemungkinan distribusi).")
    atr = latest.get("ATR", 1)
    if atr / latest.get("Close", 1) > 0.08:
        reasons.append("Volatilitas ekstrem (>8% per hari).")
    if change_pct > 15:
        reasons.append(f"Kenaikan terlalu tajam (+{change_pct:.1f}%). Rawan koreksi.")
    if change_pct < -10:
        reasons.append(f"Penurunan tajam ({change_pct:.1f}%). Sedang dalam tekanan jual.")

    return len(reasons) > 0, reasons


# ═══════════════════════════════════════════════════════════════════
# 5. FINAL SCORING
# ═══════════════════════════════════════════════════════════════════
def calculate_opportunity_score(
    tradeability, volume_score, momentum_score, entry_score,
    rr_score, news_score, ml_score,
    is_overextended=False, is_high_risk=False,
) -> float:
    """
    Final 0-100 score.
    Weights: Tradeability 15%, Volume 15%, Momentum 15%, Entry 15%,
             Technical 15%, R/R 10%, News 5%, ML 5%, Market 5%
    """
    raw = (
        (tradeability / 100) * 15 +
        (volume_score / 15) * 15 +
        (momentum_score / 15) * 15 +
        (entry_score / 100) * 15 +
        (rr_score / 20) * 10 +
        (news_score / 5) * 5 +
        (ml_score / 5) * 5
    )

    # Penalties
    if is_overextended:
        raw *= 0.7
    if is_high_risk:
        raw *= 0.6

    return round(min(max(raw, 0), 100), 1)


# ═══════════════════════════════════════════════════════════════════
# 6. "WHY THIS STOCK?" & "WHAT SHOULD I WATCH?"
# ═══════════════════════════════════════════════════════════════════
def generate_why_this_stock(cand: dict) -> dict:
    """Generate the ✓ reasons and ⚠ concerns checklist."""
    reasons = []
    concerns = []

    va = cand["Volume_Analysis"]
    mom = cand["Momentum"]
    vwap = cand["VWAP"]
    sr = cand["Support_Resistance"]
    rr = cand["Risk_Reward"]
    news = cand["News"]
    pa = cand["Price_Action"]

    # Reasons
    if va["rvol"] > 1.5:
        reasons.append(f"Volume {va['rvol']:.1f}x di atas rata-rata")
    if vwap.get("available") and vwap["position"] == "ABOVE":
        reasons.append("Harga di atas VWAP")
    if mom["strength"] in ["STRONG", "MODERATE"]:
        reasons.append(f"Momentum {mom['strength'].lower()}")
    if mom["trend"] == "UP":
        reasons.append("Tren jangka pendek naik (uptrend)")
    if sr["dist_support_pct"] < 3:
        reasons.append(f"Dekat area support (jarak {sr['dist_support_pct']:.1f}%)")
    if rr["ratio"] >= 1.5:
        reasons.append(f"Risk/Reward {rr['display']}")
    if news["impact"] in ["POSITIVE", "SLIGHT_POSITIVE"]:
        reasons.append(f"Sentimen berita {news['impact'].lower()}")
    if "BREAKOUT" in pa.get("patterns", []):
        reasons.append("Breakout terdeteksi")

    # Concerns
    if cand["Change_Pct"] > 5:
        concerns.append(f"Sudah naik +{cand['Change_Pct']:.1f}% hari ini")
    if sr["dist_resistance_pct"] < 2:
        concerns.append(f"Resistance hanya {sr['dist_resistance_pct']:.1f}% di atas")
    if mom["rsi"] > 70:
        concerns.append(f"RSI mendekati overbought ({mom['rsi']:.0f})")
    if cand["High_Risk"]:
        for r in cand["Risk_Reasons"]:
            concerns.append(r)

    return {"reasons": reasons, "concerns": concerns}


def generate_watch_checklist(cand: dict) -> dict:
    """Generate confirmation and invalidation checklists."""
    confirmations = []
    invalidations = []

    vwap = cand["VWAP"]
    mom = cand["Momentum"]
    sr = cand["Support_Resistance"]

    # Confirmations
    if vwap.get("available"):
        confirmations.append("harga tetap di atas VWAP")
    confirmations.append("volume tetap di atas rata-rata")
    if sr["dist_resistance_pct"] < 5:
        confirmations.append("konfirmasi breakout resistance")
    confirmations.append("momentum tetap positif")

    # Invalidations
    invalidations.append(f"harga turun di bawah support (Rp {sr['support']:,.0f})")
    invalidations.append("volume menurun drastis")
    if vwap.get("available"):
        invalidations.append("harga breakdown di bawah VWAP")
    invalidations.append("kondisi pasar memburuk secara keseluruhan")

    return {"confirmations": confirmations, "invalidations": invalidations}


# ═══════════════════════════════════════════════════════════════════
# 7. LEGACY COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════
def get_scanner_explanation(cand: dict) -> str:
    """Legacy compatibility: simple text explanation."""
    why = generate_why_this_stock(cand)
    parts = []
    for r in why["reasons"][:3]:
        parts.append(r)
    if why["concerns"]:
        parts.append(f"Perhatian: {why['concerns'][0]}")
    return ". ".join(parts) + "." if parts else "Saham menunjukkan setup teknikal yang stabil."

