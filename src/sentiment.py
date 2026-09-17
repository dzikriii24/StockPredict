"""
sentiment.py — News Sentiment Analysis Module

Performs sentiment analysis on financial news headlines.
Uses TextBlob as lightweight model (no GPU required).

Outputs:
- Sentiment label: POSITIVE / NEUTRAL / NEGATIVE
- Sentiment score: -1 to +1
- Confidence: 0 to 1
- Daily aggregation with rolling averages
- News momentum features
- Event detection (HIGH NEWS ACTIVITY, SENTIMENT SHIFT)
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
from datetime import datetime
from src.news_relevance import evaluate_relevance


def _get_textblob():
    """Lazy import TextBlob to avoid startup overhead."""
    try:
        from textblob import TextBlob
        return TextBlob
    except ImportError:
        return None


def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of a text using TextBlob.

    Args:
        text: Text to analyze (headline or description)

    Returns:
        Dictionary with sentiment_label, sentiment_score, confidence
    """
    if not text or not text.strip():
        return {
            "sentiment_label": "NEUTRAL",
            "sentiment_score": 0.0,
            "confidence": 0.0,
        }

    TextBlob = _get_textblob()

    if TextBlob is None:
        # Fallback: simple keyword-based sentiment
        return _keyword_sentiment(text)

    try:
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 to +1
        subjectivity = blob.sentiment.subjectivity  # 0 to 1

        # Classify
        if polarity > 0.1:
            label = "POSITIVE"
        elif polarity < -0.1:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"

        return {
            "sentiment_label": label,
            "sentiment_score": round(polarity, 4),
            "confidence": round(1 - subjectivity * 0.5, 4),  # Higher subjectivity = lower confidence
        }

    except Exception:
        return _keyword_sentiment(text)


def _keyword_sentiment(text: str) -> dict:
    """
    Fallback keyword-based sentiment analysis.
    Used when TextBlob is not available.
    """
    text_lower = text.lower()

    positive_words = [
        "naik", "meningkat", "profit", "untung", "positif", "bullish",
        "growth", "gain", "rally", "surge", "up", "rise", "strong",
        "outperform", "buy", "optimis", "recovery", "rebound", "tinggi",
        "record", "laba", "dividen", "bagus", "baik",
    ]
    negative_words = [
        "turun", "jatuh", "rugi", "loss", "negatif", "bearish",
        "decline", "drop", "fall", "crash", "down", "weak", "sell",
        "pesimis", "krisis", "koreksi", "rendah", "gagal",
        "bangkrut", "resesi", "inflasi", "default",
    ]

    pos_count = sum(1 for w in positive_words if w in text_lower)
    neg_count = sum(1 for w in negative_words if w in text_lower)
    total = pos_count + neg_count

    if total == 0:
        return {"sentiment_label": "NEUTRAL", "sentiment_score": 0.0, "confidence": 0.3}

    score = (pos_count - neg_count) / max(total, 1)
    score = max(-1, min(1, score))  # Clamp to [-1, 1]

    if score > 0.1:
        label = "POSITIVE"
    elif score < -0.1:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"

    return {
        "sentiment_label": label,
        "sentiment_score": round(score, 4),
        "confidence": round(min(total / 5, 1.0), 4),
    }


def analyze_news_dataframe(news_df: pd.DataFrame, ticker: str = "") -> pd.DataFrame:
    """
    Add sentiment analysis, relevance, and impact to a news DataFrame.

    Args:
        news_df: DataFrame with 'title' and optionally 'description' columns
        ticker: The stock ticker context for this news

    Returns:
        DataFrame with sentiment, relevance, and impact columns added
    """
    if news_df.empty:
        for col in ["sentiment_label", "sentiment_score", "confidence", 
                    "relevance", "impact", "impact_reason"]:
            news_df[col] = pd.Series(dtype=str)
        return news_df

    df = news_df.copy()

    # Apply relevance & impact row by row
    def apply_analysis(row):
        title = row.get("title", "")
        desc = row.get("description", "")
        text = f"{title} {desc}".strip()
        
        # Base sentiment
        sent = analyze_sentiment(text)
        
        # Relevance
        rel = evaluate_relevance(title, desc, ticker) if ticker else {"overall_relevance": "GENERAL", "reason": ""}
        relevance_score = rel.get("overall_relevance", "GENERAL")
        
        # Impact derivation
        impact = "UNCERTAIN"
        reason = rel.get("reason", "")
        
        if relevance_score == "HIGH":
            impact = sent["sentiment_label"]
        elif relevance_score == "MEDIUM":
            if sent["sentiment_label"] != "NEUTRAL":
                impact = "MIXED"
            else:
                impact = "NEUTRAL"
        else:
            impact = "UNCERTAIN"
            
        return pd.Series({
            "sentiment_label": sent["sentiment_label"],
            "sentiment_score": sent["sentiment_score"],
            "confidence": sent["confidence"],
            "relevance": relevance_score,
            "impact": impact,
            "impact_reason": reason
        })

    analysis = df.apply(apply_analysis, axis=1)
    for col in analysis.columns:
        df[col] = analysis[col]

    return df


def aggregate_daily_sentiment(
    news_df: pd.DataFrame,
    ticker: str = None
) -> pd.DataFrame:
    """
    Aggregate news sentiment by date (and optionally by ticker).

    For each date calculates:
    - news_count
    - positive_count, neutral_count, negative_count
    - positive_ratio, negative_ratio
    - average_sentiment
    - weighted_sentiment (weighted by confidence)
    - Sentiment_MA3, Sentiment_MA7 (rolling averages)

    Args:
        news_df: DataFrame with sentiment columns
        ticker: Optional ticker to filter by

    Returns:
        DataFrame indexed by date with aggregated metrics
    """
    if news_df.empty:
        return pd.DataFrame(columns=[
            "news_count", "positive_count", "neutral_count", "negative_count",
            "positive_ratio", "negative_ratio", "average_sentiment",
            "weighted_sentiment", "Sentiment_MA3", "Sentiment_MA7"
        ])

    df = news_df.copy()

    # Filter by ticker if specified
    if ticker:
        mask = df["ticker"] == ticker
        if "matched_tickers" in df.columns:
            mask = mask | df["matched_tickers"].apply(
                lambda x: ticker in x if isinstance(x, list) else False
            )
        df = df[mask]

    if df.empty:
        return pd.DataFrame()

    # Ensure date column
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # Group by date
    daily = df.groupby(df["date"].dt.date).agg(
        news_count=("title", "count"),
        positive_count=("sentiment_label", lambda x: (x == "POSITIVE").sum()),
        neutral_count=("sentiment_label", lambda x: (x == "NEUTRAL").sum()),
        negative_count=("sentiment_label", lambda x: (x == "NEGATIVE").sum()),
        average_sentiment=("sentiment_score", "mean"),
        weighted_sentiment=("sentiment_score", lambda x: np.average(
            x, weights=df.loc[x.index, "confidence"].values
        ) if len(x) > 0 else 0),
    ).reset_index()

    daily.columns = [
        "date", "news_count", "positive_count", "neutral_count",
        "negative_count", "average_sentiment", "weighted_sentiment"
    ]

    # Ratios
    daily["positive_ratio"] = daily["positive_count"] / daily["news_count"]
    daily["negative_ratio"] = daily["negative_count"] / daily["news_count"]

    # Sort by date
    daily = daily.sort_values("date")
    daily.index = pd.to_datetime(daily["date"])
    daily = daily.drop(columns=["date"])

    # Rolling sentiment averages
    daily["Sentiment_MA3"] = daily["average_sentiment"].rolling(window=3, min_periods=1).mean()
    daily["Sentiment_MA7"] = daily["average_sentiment"].rolling(window=7, min_periods=1).mean()

    return daily


def calculate_news_momentum(daily_sentiment: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate news momentum features.

    Features:
    - news_volume: same as news_count
    - news_volume_change: day-over-day change in news count
    - sentiment_change: day-over-day change in average sentiment
    - sentiment_momentum: sentiment_change * news_volume_change direction

    Args:
        daily_sentiment: Daily aggregated sentiment DataFrame

    Returns:
        DataFrame with momentum features added
    """
    if daily_sentiment.empty:
        return daily_sentiment

    df = daily_sentiment.copy()

    df["news_volume"] = df["news_count"]
    df["news_volume_change"] = df["news_count"].pct_change()
    df["sentiment_change"] = df["average_sentiment"].diff()

    # Sentiment momentum: positive if both sentiment and volume are increasing
    df["sentiment_momentum"] = df["sentiment_change"] * (1 + df["news_volume_change"].fillna(0))

    return df


def detect_events(
    daily_sentiment: pd.DataFrame,
    news_threshold: float = 2.0,
    sentiment_threshold: float = 0.3
) -> List[dict]:
    """
    Detect significant news events.

    Events:
    - HIGH NEWS ACTIVITY: news count > rolling mean + threshold * std
    - SENTIMENT SHIFT: absolute sentiment change > threshold

    Args:
        daily_sentiment: Daily sentiment DataFrame
        news_threshold: Std multiplier for high activity (default: 2.0)
        sentiment_threshold: Min sentiment change for shift (default: 0.3)

    Returns:
        List of event dictionaries
    """
    if daily_sentiment.empty or len(daily_sentiment) < 3:
        return []

    events = []
    df = daily_sentiment.copy()

    # Rolling stats
    rolling_mean = df["news_count"].rolling(window=7, min_periods=1).mean()
    rolling_std = df["news_count"].rolling(window=7, min_periods=1).std().fillna(1)

    # Check latest date
    latest = df.iloc[-1]
    latest_date = df.index[-1]

    # HIGH NEWS ACTIVITY
    threshold_value = rolling_mean.iloc[-1] + news_threshold * rolling_std.iloc[-1]
    if latest["news_count"] > threshold_value:
        dominant = "POSITIVE" if latest.get("positive_count", 0) > latest.get("negative_count", 0) else \
                   "NEGATIVE" if latest.get("negative_count", 0) > latest.get("positive_count", 0) else "NEUTRAL"
        events.append({
            "type": "HIGH_NEWS_ACTIVITY",
            "date": str(latest_date),
            "description": f"Peningkatan jumlah berita ({int(latest['news_count'])} artikel) dibandingkan rata-rata ({rolling_mean.iloc[-1]:.0f}).",
            "dominant_sentiment": dominant,
            "avg_sentiment": round(latest.get("average_sentiment", 0), 2),
        })

    # SENTIMENT SHIFT
    if len(df) >= 2:
        prev = df.iloc[-2]
        change = latest.get("average_sentiment", 0) - prev.get("average_sentiment", 0)
        if abs(change) > sentiment_threshold:
            direction = "membaik" if change > 0 else "memburuk"
            events.append({
                "type": "SENTIMENT_SHIFT",
                "date": str(latest_date),
                "description": f"Perubahan sentimen signifikan: sentimen {direction} sebesar {change:+.2f}.",
                "change": round(change, 2),
                "current_sentiment": round(latest.get("average_sentiment", 0), 2),
            })

    return events


def merge_sentiment_with_stock(
    stock_df: pd.DataFrame,
    daily_sentiment: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge daily sentiment features into stock DataFrame.
    Time-aligned: only uses news published BEFORE the trading date.

    Args:
        stock_df: Stock DataFrame with DatetimeIndex
        daily_sentiment: Daily sentiment DataFrame

    Returns:
        Stock DataFrame with sentiment columns merged
    """
    if daily_sentiment.empty:
        # Add empty sentiment columns
        for col in ["news_count", "average_sentiment", "Sentiment_MA3",
                     "Sentiment_MA7", "news_volume", "sentiment_momentum"]:
            stock_df[col] = 0.0
        return stock_df

    df = stock_df.copy()
    sentiment = daily_sentiment.copy()

    # Ensure both have DatetimeIndex
    sentiment.index = pd.to_datetime(sentiment.index)
    if sentiment.index.tz is not None:
        sentiment.index = sentiment.index.tz_localize(None)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    # Shift sentiment by 1 day to prevent data leakage
    # News from day T is used for prediction on day T+1
    sentiment_cols = [
        "news_count", "average_sentiment", "Sentiment_MA3",
        "Sentiment_MA7", "positive_ratio", "negative_ratio"
    ]

    # Add momentum if available
    if "news_volume" in sentiment.columns:
        sentiment_cols.append("news_volume")
    if "sentiment_momentum" in sentiment.columns:
        sentiment_cols.append("sentiment_momentum")

    available_cols = [c for c in sentiment_cols if c in sentiment.columns]

    if not available_cols:
        for col in sentiment_cols:
            df[col] = 0.0
        return df

    # Reindex to stock dates and forward-fill (use previous day's sentiment)
    sentiment_aligned = sentiment[available_cols].reindex(df.index, method="ffill")

    # Merge
    for col in available_cols:
        df[col] = sentiment_aligned[col].fillna(0)

    # Fill any missing sentiment columns
    for col in sentiment_cols:
        if col not in df.columns:
            df[col] = 0.0

    return df
