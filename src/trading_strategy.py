"""
trading_strategy.py — Trading Signal Generation

Combines technical analysis and ML predictions
to generate BUY/SELL/HOLD signals with configurable thresholds.
"""

import pandas as pd
import numpy as np
from typing import Optional
from src.screener import calculate_technical_score


def generate_signal(
    tech_score: int,
    prediction: str,
    prob_up: float,
    threshold: float = 0.6
) -> str:
    """
    Generate trading signal based on technical score and ML prediction.

    Rules:
        BUY:  tech_score >= 4 AND prediction == UP AND prob_up >= threshold
        SELL: prediction == DOWN AND prob_down >= threshold (i.e., prob_up < 1 - threshold)
        HOLD: otherwise

    Args:
        tech_score: Technical analysis score (0-5)
        prediction: ML prediction ('UP' or 'DOWN')
        prob_up: Probability of price going UP
        threshold: Minimum probability threshold (default: 0.6)

    Returns:
        Signal string: 'BUY', 'SELL', or 'HOLD'
    """
    if tech_score >= 4 and prediction == "UP" and prob_up >= threshold:
        return "BUY"
    elif prediction == "DOWN" and prob_up < (1 - threshold):
        return "SELL"
    else:
        return "HOLD"


def generate_signals_series(
    df: pd.DataFrame,
    model,
    feature_columns: list,
    threshold: float = 0.6
) -> pd.DataFrame:
    """
    Generate signals for an entire DataFrame (used in backtesting).

    Args:
        df: DataFrame with all indicators
        model: Trained ML model
        feature_columns: Feature column names
        threshold: Signal threshold

    Returns:
        DataFrame with Signal, Predicted, Prob_UP columns added
    """
    df = df.copy()

    # Get available features
    available_features = [c for c in feature_columns if c in df.columns]
    valid_mask = df[available_features].notna().all(axis=1)
    valid_df = df[valid_mask]

    if valid_df.empty:
        df["Signal"] = "HOLD"
        df["Predicted"] = 0
        df["Prob_UP"] = 0.5
        return df

    X = valid_df[available_features].values
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)

    # Initialize columns
    df["Predicted"] = np.nan
    df["Prob_UP"] = np.nan
    df["Signal"] = "HOLD"

    df.loc[valid_mask, "Predicted"] = predictions
    prob_up_vals = probabilities[:, 1] if probabilities.shape[1] > 1 else probabilities[:, 0]
    df.loc[valid_mask, "Prob_UP"] = prob_up_vals

    # Calculate technical scores and generate signals
    for idx in valid_df.index:
        row = df.loc[idx]
        tech_score = calculate_technical_score(row)
        pred_str = "UP" if row["Predicted"] == 1 else "DOWN"
        df.loc[idx, "Signal"] = generate_signal(
            tech_score, pred_str, row["Prob_UP"], threshold
        )

    return df


def get_signal_explanation(
    signal: str,
    tech_score: int,
    prediction: str,
    prob_up: float,
    threshold: float
) -> str:
    """
    Generate human-readable explanation for a trading signal.

    Args:
        signal: The signal (BUY/SELL/HOLD)
        tech_score: Technical score
        prediction: ML prediction
        prob_up: UP probability
        threshold: Threshold used

    Returns:
        Explanation string in Indonesian
    """
    if signal == "BUY":
        return (
            f"**Signal: BUY** — Technical score tinggi ({tech_score}/5), "
            f"model memprediksi arah UP dengan probabilitas {prob_up*100:.1f}% "
            f"(di atas threshold {threshold*100:.0f}%). "
            f"Kondisi teknikal dan prediksi model mendukung posisi beli."
        )
    elif signal == "SELL":
        return (
            f"**Signal: SELL** — Model memprediksi arah DOWN dengan probabilitas "
            f"{(1-prob_up)*100:.1f}% (di atas threshold {threshold*100:.0f}%). "
            f"Technical score: {tech_score}/5. "
            f"Kondisi menunjukkan potensi penurunan harga."
        )
    else:
        return (
            f"**Signal: HOLD** — Kondisi belum memenuhi kriteria BUY atau SELL. "
            f"Technical score: {tech_score}/5, prediksi: {prediction}, "
            f"probabilitas UP: {prob_up*100:.1f}%. "
            f"Disarankan menunggu konfirmasi lebih lanjut."
        )


def calculate_entry_target_stoploss(
    current_price: float,
    prediction: str,
    support: float,
    resistance: float,
    atr_pct: float = 2.0
) -> dict:
    """
    Calculate entry price, target, and stop loss.

    For BUY signals:
        Entry = current price
        Target = resistance level or current + ATR%
        Stop Loss = support level or current - ATR%

    Args:
        current_price: Current stock price
        prediction: UP or DOWN
        support: Support level
        resistance: Resistance level
        atr_pct: Fallback ATR percentage for target/SL (default: 2%)

    Returns:
        Dictionary with entry, target, stop_loss
    """
    entry = current_price

    if prediction == "UP":
        # Target: resistance or +ATR%
        target = max(resistance, entry * (1 + atr_pct / 100))
        # Stop loss: support or -ATR%
        stop_loss = min(support, entry * (1 - atr_pct / 100))
    else:
        # For DOWN prediction, still calculate based on defensive positioning
        target = entry * (1 + atr_pct / 100)  # modest target
        stop_loss = entry * (1 - atr_pct * 1.5 / 100)  # wider stop loss

    # Ensure stop loss is below entry
    if stop_loss >= entry:
        stop_loss = entry * (1 - atr_pct / 100)

    # Ensure target is above entry
    if target <= entry:
        target = entry * (1 + atr_pct / 100)

    return {
        "entry_price": round(entry, 0),
        "target_price": round(target, 0),
        "stop_loss": round(stop_loss, 0),
    }


def generate_technical_signals_series(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate basic technical signals for backtesting.
    BUY when EMA20 crosses above EMA50 or RSI crosses above 30.
    SELL when EMA20 crosses below EMA50 or RSI crosses below 70.
    """
    df = df.copy()
    df["Signal"] = "HOLD"
    
    # Calculate required indicators if not present
    if "EMA20" not in df.columns:
        df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    if "EMA50" not in df.columns:
        df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
        
    for i in range(1, len(df)):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        
        # BUY: EMA20 crosses above EMA50 OR RSI crosses above 30
        ema_cross_up = prev["EMA20"] <= prev["EMA50"] and curr["EMA20"] > curr["EMA50"]
        rsi_cross_up = prev.get("RSI", 50) <= 30 and curr.get("RSI", 50) > 30
        
        # SELL: EMA20 crosses below EMA50 OR RSI crosses below 70
        ema_cross_down = prev["EMA20"] >= prev["EMA50"] and curr["EMA20"] < curr["EMA50"]
        rsi_cross_down = prev.get("RSI", 50) >= 70 and curr.get("RSI", 50) < 70
        
        if ema_cross_up or rsi_cross_up:
            df.iloc[i, df.columns.get_loc("Signal")] = "BUY"
        elif ema_cross_down or rsi_cross_down:
            df.iloc[i, df.columns.get_loc("Signal")] = "SELL"
            
    return df
