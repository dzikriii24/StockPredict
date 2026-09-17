"""
screener.py — Stock Screening Module

Compares multiple stocks using technical scores,
ML predictions, and generates a sortable screening table.
Now includes Stock Ranking based on ML Prediction Probability.
"""

import pandas as pd
import numpy as np
from typing import List, Optional

from src.data_loader import fetch_stock_data, get_ticker_name
from src.preprocessing import prepare_data
from src.indicators import add_all_indicators
from src.prediction import train_model, predict_latest


def calculate_technical_score(row: pd.Series) -> int:
    """
    Calculate transparent technical score (0-5) for a stock.
    """
    score = 0
    if pd.notna(row.get("MA20")) and pd.notna(row.get("MA50")):
        if row["MA20"] > row["MA50"]:
            score += 1
    if pd.notna(row.get("Close")) and pd.notna(row.get("MA20")):
        if row["Close"] > row["MA20"]:
            score += 1
    if pd.notna(row.get("RSI")):
        if 30 <= row["RSI"] <= 70:
            score += 1
    if pd.notna(row.get("MACD")) and pd.notna(row.get("MACD_Signal")):
        if row["MACD"] > row["MACD_Signal"]:
            score += 1
    if pd.notna(row.get("Volume_Ratio")):
        if row["Volume_Ratio"] > 1:
            score += 1
    return score


def get_score_breakdown(row: pd.Series) -> dict:
    """Get detailed breakdown of technical score."""
    breakdown = {}
    
    if pd.notna(row.get("MA20")) and pd.notna(row.get("MA50")):
        passed = row["MA20"] > row["MA50"]
        breakdown["MA20 > MA50"] = {"passed": passed, "value": f"MA20={row['MA20']:.0f}, MA50={row['MA50']:.0f}"}
    else:
        breakdown["MA20 > MA50"] = {"passed": False, "value": "N/A"}

    if pd.notna(row.get("Close")) and pd.notna(row.get("MA20")):
        passed = row["Close"] > row["MA20"]
        breakdown["Price > MA20"] = {"passed": passed, "value": f"Price={row['Close']:.0f}, MA20={row['MA20']:.0f}"}
    else:
        breakdown["Price > MA20"] = {"passed": False, "value": "N/A"}

    if pd.notna(row.get("RSI")):
        passed = 30 <= row["RSI"] <= 70
        breakdown["RSI 30-70"] = {"passed": passed, "value": f"RSI={row['RSI']:.1f}"}
    else:
        breakdown["RSI 30-70"] = {"passed": False, "value": "N/A"}

    if pd.notna(row.get("MACD")) and pd.notna(row.get("MACD_Signal")):
        passed = row["MACD"] > row["MACD_Signal"]
        breakdown["MACD > Signal"] = {"passed": passed, "value": f"MACD={row['MACD']:.2f}, Signal={row['MACD_Signal']:.2f}"}
    else:
        breakdown["MACD > Signal"] = {"passed": False, "value": "N/A"}

    if pd.notna(row.get("Volume_Ratio")):
        passed = row["Volume_Ratio"] > 1
        breakdown["Volume Ratio > 1"] = {"passed": passed, "value": f"Ratio={row['Volume_Ratio']:.2f}"}
    else:
        breakdown["Volume Ratio > 1"] = {"passed": False, "value": "N/A"}

    return breakdown


def classify_trend(row: pd.Series) -> str:
    """Classify stock trend based on indicators."""
    score = row.get("Technical_Score", 0)
    if score >= 4:
        return "🟢 Bullish"
    elif score >= 3:
        return "🟡 Neutral"
    elif score >= 2:
        return "🟠 Neutral"
    else:
        return "🔴 Bearish"


def rank_stocks(screen_results: pd.DataFrame) -> pd.DataFrame:
    """
    Rank stocks based on Prob. UP (%) and Technical Score.
    """
    if screen_results.empty:
        return screen_results
        
    df = screen_results.copy()
    
    # Exclude errors
    df = df[df["Trend"] != "❌ Error"]
    
    if df.empty:
        return df
        
    # Sort primarily by Probability UP, then by Technical Score
    df = df.sort_values(by=["Prob. UP (%)", "Technical_Score"], ascending=[False, False])
    
    # Add Rank column
    df.insert(0, "Rank", range(1, len(df) + 1))
    
    return df


def screen_stocks(
    tickers: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    progress_callback=None
) -> pd.DataFrame:
    """
    Screen multiple stocks and generate comparison table.
    Note: For the screener, we use the Technical Model for speed, 
    but macro/news could be injected if provided.
    """
    results = []

    for i, ticker in enumerate(tickers):
        if progress_callback:
            progress_callback(i / len(tickers), f"Analyzing {ticker}...")

        try:
            raw_data = fetch_stock_data(ticker, start_date, end_date)
            df = prepare_data(raw_data)
            df = add_all_indicators(df)

            latest = df.iloc[-1]
            tech_score = calculate_technical_score(latest)

            try:
                # Train baseline model for screener to ensure speed
                ml_result = train_model(df, ticker)
                prediction = predict_latest(
                    df, ml_result["model"], ml_result["feature_columns"]
                )
                ml_pred = prediction["prediction"]
                prob_up = prediction["prob_up"]
            except Exception:
                ml_pred = "N/A"
                prob_up = 0.5

            daily_return = latest.get("Daily_Return", 0)

            if tech_score >= 4 and ml_pred == "UP" and prob_up >= 0.6:
                signal = "🟢 BUY"
            elif ml_pred == "DOWN" and prob_up < 0.4:
                signal = "🔴 SELL"
            else:
                signal = "🟡 HOLD"

            results.append({
                "Ticker": ticker,
                "Name": get_ticker_name(ticker),
                "Price": latest["Close"],
                "Daily Return (%)": round(daily_return, 2),
                "Technical_Score": tech_score,
                "Trend": classify_trend(pd.Series({"Technical_Score": tech_score})),
                "ML Prediction": ml_pred,
                "Prob. UP (%)": round(prob_up * 100, 1),
                "Signal": signal,
            })

        except Exception as e:
            results.append({
                "Ticker": ticker,
                "Name": get_ticker_name(ticker),
                "Price": None,
                "Daily Return (%)": None,
                "Technical_Score": None,
                "Trend": "❌ Error",
                "ML Prediction": "Error",
                "Prob. UP (%)": None,
                "Signal": f"Error: {str(e)[:30]}",
            })

    if progress_callback:
        progress_callback(1.0, "Screening complete!")

    df_results = pd.DataFrame(results)
    
    # Rank them automatically
    ranked_results = rank_stocks(df_results)
    
    return ranked_results if not ranked_results.empty else df_results
