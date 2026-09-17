"""
visualization.py — Interactive Plotly Charts

Generates all charts for the Streamlit dashboard:
Candlestick, Volume, RSI, MACD, Bollinger Bands,
Prediction, Equity Curve, Drawdown.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


# ─── Color Palette ───────────────────────────────────────────────
COLORS = {
    "bg": "#0e1117",
    "card_bg": "#1a1d23",
    "text": "#fafafa",
    "text_secondary": "#8b949e",
    "green": "#00d084",
    "red": "#ff6b6b",
    "blue": "#4ecdc4",
    "purple": "#a78bfa",
    "orange": "#f59e0b",
    "yellow": "#fbbf24",
    "ma20": "#4ecdc4",
    "ma50": "#f59e0b",
    "upper_band": "rgba(167, 139, 250, 0.3)",
    "lower_band": "rgba(167, 139, 250, 0.3)",
    "grid": "rgba(255,255,255,0.05)",
}

LAYOUT_DEFAULTS = dict(
    template="plotly_dark",
    paper_bgcolor=COLORS["bg"],
    plot_bgcolor=COLORS["card_bg"],
    font=dict(family="Inter, sans-serif", color=COLORS["text"], size=12),
    xaxis=dict(gridcolor=COLORS["grid"], showgrid=True),
    margin=dict(l=60, r=20, t=50, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    hovermode="x unified",
)

# Default yaxis settings (applied separately to avoid duplicate keyword conflicts)
YAXIS_DEFAULTS = dict(gridcolor=COLORS["grid"], showgrid=True)


def create_candlestick_chart(df: pd.DataFrame, ticker: str = "") -> go.Figure:
    """
    Chart 1 — Candlestick with MA20 & MA50 overlay.

    Args:
        df: DataFrame with OHLC, MA20, MA50
        ticker: Stock ticker for title

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name="OHLC",
        increasing_line_color=COLORS["green"],
        decreasing_line_color=COLORS["red"],
    ))

    # MA20
    if "MA20" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MA20"],
            name="MA20", line=dict(color=COLORS["ma20"], width=1.5),
        ))

    # MA50
    if "MA50" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MA50"],
            name="MA50", line=dict(color=COLORS["ma50"], width=1.5),
        ))

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        yaxis={**YAXIS_DEFAULTS, "title": "Price (Rp)"},
        title=f"📈 {ticker} — Candlestick Chart",
        xaxis_rangeslider_visible=False,
        height=500,
    )

    return fig


def create_volume_chart(df: pd.DataFrame, ticker: str = "") -> go.Figure:
    """
    Chart 2 — Volume Bar Chart + Volume MA20.

    Args:
        df: DataFrame with Volume, Volume_MA20
        ticker: Stock ticker

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    # Color bars based on price change
    colors = [
        COLORS["green"] if df["Close"].iloc[i] >= df["Open"].iloc[i]
        else COLORS["red"]
        for i in range(len(df))
    ]

    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"],
        name="Volume",
        marker_color=colors,
        opacity=0.7,
    ))

    if "Volume_MA20" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Volume_MA20"],
            name="Volume MA20",
            line=dict(color=COLORS["orange"], width=2),
        ))

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        yaxis={**YAXIS_DEFAULTS, "title": "Volume"},
        title=f"📊 {ticker} — Volume",
        height=300,
    )

    return fig


def create_rsi_chart(df: pd.DataFrame, ticker: str = "") -> go.Figure:
    """
    Chart 3 — RSI with 30/70 lines.

    Args:
        df: DataFrame with RSI column
        ticker: Stock ticker

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["RSI"],
            name="RSI(14)",
            line=dict(color=COLORS["purple"], width=2),
        ))

    # Overbought line (70)
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["red"],
                  annotation_text="Overbought (70)", annotation_position="right")

    # Oversold line (30)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["green"],
                  annotation_text="Oversold (30)", annotation_position="right")

    # Neutral line (50)
    fig.add_hline(y=50, line_dash="dot", line_color=COLORS["text_secondary"],
                  opacity=0.5)

    # Shade overbought/oversold zones
    fig.add_hrect(y0=70, y1=100, fillcolor=COLORS["red"], opacity=0.05)
    fig.add_hrect(y0=0, y1=30, fillcolor=COLORS["green"], opacity=0.05)

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        yaxis=dict(range=[0, 100], gridcolor=COLORS["grid"], showgrid=True, title="RSI"),
        title=f"📉 {ticker} — RSI (Relative Strength Index)",
        height=300,
    )

    return fig


def create_macd_chart(df: pd.DataFrame, ticker: str = "") -> go.Figure:
    """
    Chart 4 — MACD + Signal + Histogram.

    Args:
        df: DataFrame with MACD, MACD_Signal, MACD_Hist
        ticker: Stock ticker

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    if "MACD_Hist" in df.columns:
        colors = [
            COLORS["green"] if v >= 0 else COLORS["red"]
            for v in df["MACD_Hist"]
        ]
        fig.add_trace(go.Bar(
            x=df.index, y=df["MACD_Hist"],
            name="Histogram",
            marker_color=colors,
            opacity=0.6,
        ))

    if "MACD" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD"],
            name="MACD",
            line=dict(color=COLORS["blue"], width=2),
        ))

    if "MACD_Signal" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD_Signal"],
            name="Signal",
            line=dict(color=COLORS["orange"], width=2),
        ))

    fig.add_hline(y=0, line_dash="dot", line_color=COLORS["text_secondary"], opacity=0.5)

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        yaxis={**YAXIS_DEFAULTS, "title": "MACD"},
        title=f"📊 {ticker} — MACD",
        height=300,
    )

    return fig


def create_bollinger_chart(df: pd.DataFrame, ticker: str = "") -> go.Figure:
    """
    Chart 5 — Bollinger Bands.

    Args:
        df: DataFrame with Close, BB_Upper, BB_Middle, BB_Lower
        ticker: Stock ticker

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    # Upper band
    if "BB_Upper" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Upper"],
            name="Upper Band",
            line=dict(color=COLORS["purple"], width=1, dash="dash"),
        ))

    # Lower band (fill between)
    if "BB_Lower" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Lower"],
            name="Lower Band",
            line=dict(color=COLORS["purple"], width=1, dash="dash"),
            fill="tonexty",
            fillcolor="rgba(167, 139, 250, 0.1)",
        ))

    # Middle band
    if "BB_Middle" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_Middle"],
            name="SMA20",
            line=dict(color=COLORS["purple"], width=1, dash="dot"),
        ))

    # Close price
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"],
        name="Close",
        line=dict(color=COLORS["blue"], width=2),
    ))

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        yaxis={**YAXIS_DEFAULTS, "title": "Price (Rp)"},
        title=f"📈 {ticker} — Bollinger Bands",
        height=400,
    )

    return fig


def create_prediction_chart(
    df: pd.DataFrame,
    test_results: pd.DataFrame = None,
    ticker: str = "",
    future_prediction: dict = None,
    interval: str = "1d"
) -> go.Figure:
    """
    Chart 6 — Prediction: actual price + predicted direction + signals.

    Args:
        df: Full DataFrame with Close
        test_results: Test period results with Predicted, Signal columns
        future_prediction: Future prediction dictionary
        interval: Time interval string
        ticker: Stock ticker

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    # Actual price
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"],
        name="Actual Price",
        line=dict(color=COLORS["text_secondary"], width=1.5),
    ))

    if test_results is not None and not test_results.empty:
        # Test period price (highlighted)
        fig.add_trace(go.Scatter(
            x=test_results.index, y=test_results["Close"],
            name="Test Period",
            line=dict(color=COLORS["blue"], width=2),
        ))
        
        # Regression Target Price
        if "Predicted_Price" in test_results.columns:
            fig.add_trace(go.Scatter(
                x=test_results.index, y=test_results["Predicted_Price"],
                name="AI Target Price",
                line=dict(color=COLORS["purple"], width=2, dash="dot"),
            ))

        # BUY signals
        if "Signal" in test_results.columns:
            buys = test_results[test_results["Signal"] == "BUY"]
            if not buys.empty:
                fig.add_trace(go.Scatter(
                    x=buys.index, y=buys["Close"],
                    mode="markers",
                    name="BUY Signal",
                    marker=dict(color=COLORS["green"], size=12, symbol="triangle-up"),
                ))

            # SELL signals
            sells = test_results[test_results["Signal"] == "SELL"]
            if not sells.empty:
                fig.add_trace(go.Scatter(
                    x=sells.index, y=sells["Close"],
                    mode="markers",
                    name="SELL Signal",
                    marker=dict(color=COLORS["red"], size=12, symbol="triangle-down"),
                ))
                
    # Plot Future Prediction Point
    if future_prediction and future_prediction.get("predicted_price"):
        try:
            last_date = df.index[-1]
            
            # Determine time delta based on interval
            if interval == "1m":
                delta = pd.Timedelta(minutes=1)
            elif interval == "5m":
                delta = pd.Timedelta(minutes=5)
            elif interval == "15m":
                delta = pd.Timedelta(minutes=15)
            elif interval == "1h":
                delta = pd.Timedelta(hours=1)
            else:
                delta = pd.Timedelta(days=1)
                
            future_date = last_date + delta
            
            # Draw line from last price to future predicted price
            fig.add_trace(go.Scatter(
                x=[last_date, future_date],
                y=[future_prediction.get("current_price", df["Close"].iloc[-1]), future_prediction["predicted_price"]],
                mode="lines+markers",
                name="AI Future Target",
                line=dict(color=COLORS["purple"], width=2, dash="dash"),
                marker=dict(color=COLORS["purple"], size=8, symbol="star")
            ))
        except Exception as e:
            print(f"Error plotting future target: {e}")

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        yaxis={**YAXIS_DEFAULTS, "title": "Price (Rp)"},
        title=f"🤖 {ticker} — ML Prediction & Signals",
        height=450,
    )

    return fig


def create_equity_curve(
    strategy_equity: pd.DataFrame,
    buy_hold_equity: pd.DataFrame = None,
    ticker: str = ""
) -> go.Figure:
    """
    Chart 7 — Equity Curve: Trading Strategy vs Buy & Hold.

    Args:
        strategy_equity: Strategy equity curve DataFrame
        buy_hold_equity: Buy & Hold equity curve DataFrame
        ticker: Stock ticker

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    if not strategy_equity.empty and "equity" in strategy_equity.columns:
        fig.add_trace(go.Scatter(
            x=strategy_equity.index, y=strategy_equity["equity"],
            name="ML + Technical Strategy",
            line=dict(color=COLORS["blue"], width=2),
            fill="tozeroy",
            fillcolor="rgba(78, 205, 196, 0.1)",
        ))

    if buy_hold_equity is not None and not buy_hold_equity.empty and "equity" in buy_hold_equity.columns:
        fig.add_trace(go.Scatter(
            x=buy_hold_equity.index, y=buy_hold_equity["equity"],
            name="Buy & Hold",
            line=dict(color=COLORS["orange"], width=2, dash="dash"),
        ))

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        yaxis={**YAXIS_DEFAULTS, "title": "Portfolio Value (Rp)"},
        title=f"💰 {ticker} — Equity Curve Comparison",
        height=400,
    )

    return fig


def create_drawdown_chart(
    equity_df: pd.DataFrame,
    ticker: str = ""
) -> go.Figure:
    """
    Chart 8 — Historical Drawdown.

    Args:
        equity_df: Equity curve DataFrame
        ticker: Stock ticker

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    if not equity_df.empty and "equity" in equity_df.columns:
        equity = equity_df["equity"]
        rolling_max = equity.cummax()
        drawdown = (equity - rolling_max) / rolling_max * 100

        fig.add_trace(go.Scatter(
            x=equity_df.index, y=drawdown,
            name="Drawdown",
            line=dict(color=COLORS["red"], width=1.5),
            fill="tozeroy",
            fillcolor="rgba(255, 107, 107, 0.2)",
        ))

    fig.add_hline(y=0, line_color=COLORS["text_secondary"], line_width=1)

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        yaxis={**YAXIS_DEFAULTS, "title": "Drawdown (%)"},
        title=f"📉 {ticker} — Drawdown",
        height=300,
    )

    return fig


def create_confusion_matrix_chart(cm, labels=None) -> go.Figure:
    """
    Create a confusion matrix heatmap.

    Args:
        cm: Confusion matrix array
        labels: Class labels (default: ['DOWN', 'UP'])

    Returns:
        Plotly Figure
    """
    if labels is None:
        labels = ["DOWN (0)", "UP (1)"]

    fig = go.Figure(data=go.Heatmap(
        z=cm,
        x=labels,
        y=labels,
        text=cm,
        texttemplate="%{text}",
        textfont=dict(size=18, color="white"),
        colorscale=[[0, "#1a1d23"], [1, "#4ecdc4"]],
        showscale=False,
    ))

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        yaxis={**YAXIS_DEFAULTS, "title": "Actual"},
        title="Confusion Matrix",
        xaxis_title="Predicted",
        height=350,
        width=400,
    )

    return fig


def create_feature_importance_chart(feature_importance: dict) -> go.Figure:
    """
    Create a horizontal bar chart of feature importance.

    Args:
        feature_importance: Dictionary of feature -> importance

    Returns:
        Plotly Figure
    """
    # Sort by importance
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    names = [f[0] for f in sorted_features]
    values = [f[1] for f in sorted_features]

    fig = go.Figure(go.Bar(
        x=values,
        y=names,
        orientation="h",
        marker_color=COLORS["blue"],
        marker_line_color=COLORS["purple"],
        marker_line_width=1,
    ))

    fig.update_layout(
        **LAYOUT_DEFAULTS,
        yaxis=dict(autorange="reversed", gridcolor=COLORS["grid"], showgrid=True),
        title="Feature Importance (Random Forest)",
        xaxis_title="Importance",
        height=400,
    )

    return fig


def create_sentiment_trend_chart(daily_sentiment: pd.DataFrame, ticker: str = "") -> go.Figure:
    """
    Chart 9 — Sentiment Trend Line Chart.
    """
    fig = go.Figure()
    
    if not daily_sentiment.empty and "average_sentiment" in daily_sentiment.columns:
        fig.add_trace(go.Scatter(
            x=daily_sentiment.index, 
            y=daily_sentiment["average_sentiment"],
            name="Daily Sentiment",
            mode="lines+markers",
            line=dict(color=COLORS["blue"], width=2),
            marker=dict(size=6)
        ))
        
        if "Sentiment_MA3" in daily_sentiment.columns:
            fig.add_trace(go.Scatter(
                x=daily_sentiment.index, 
                y=daily_sentiment["Sentiment_MA3"],
                name="3-Day MA",
                line=dict(color=COLORS["orange"], width=2, dash="dot"),
            ))
            
    fig.add_hline(y=0, line_color=COLORS["text_secondary"], line_width=1, line_dash="dash")
            
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        yaxis={**YAXIS_DEFAULTS, "title": "Sentiment Score (-1 to 1)", "range": [-1.1, 1.1]},
        title=f"📰 {ticker} — Sentiment Trend",
        height=350,
    )
    return fig


def create_news_volume_chart(daily_sentiment: pd.DataFrame, ticker: str = "") -> go.Figure:
    """
    Chart 10 — News Volume Bar Chart.
    """
    fig = go.Figure()
    
    if not daily_sentiment.empty and "news_count" in daily_sentiment.columns:
        fig.add_trace(go.Bar(
            x=daily_sentiment.index, 
            y=daily_sentiment["news_count"],
            name="News Count",
            marker_color=COLORS["purple"],
            opacity=0.8
        ))
            
    fig.update_layout(
        **LAYOUT_DEFAULTS,
        yaxis={**YAXIS_DEFAULTS, "title": "Number of Articles"},
        title=f"📊 {ticker} — News Volume",
        height=300,
    )
    return fig


def create_sentiment_distribution(daily_sentiment: pd.DataFrame, ticker: str = "") -> go.Figure:
    """
    Chart 11 — Sentiment Distribution Donut Chart.
    """
    fig = go.Figure()
    
    if not daily_sentiment.empty:
        pos = daily_sentiment["positive_count"].sum()
        neu = daily_sentiment["neutral_count"].sum()
        neg = daily_sentiment["negative_count"].sum()
        
        fig.add_trace(go.Pie(
            labels=["Positive", "Neutral", "Negative"],
            values=[pos, neu, neg],
            hole=0.6,
            marker_colors=[COLORS["green"], COLORS["text_secondary"], COLORS["red"]],
            textinfo="percent+label",
            hoverinfo="label+value+percent"
        ))
            
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["bg"],
        plot_bgcolor=COLORS["card_bg"],
        font=dict(family="Inter, sans-serif", color=COLORS["text"], size=12),
        title=f"📊 {ticker} — Overall Sentiment Distribution",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    return fig


def create_macro_chart(dates, values, returns, label: str) -> go.Figure:
    """
    Chart 12 — Macro Indicator Chart.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(
            x=dates, y=values,
            name="Value",
            line=dict(color=COLORS["blue"], width=2),
        ),
        secondary_y=False,
    )
    
    # Color bars based on daily return
    colors = [COLORS["green"] if r >= 0 else COLORS["red"] for r in returns]
    
    fig.add_trace(
        go.Bar(
            x=dates, y=returns,
            name="Daily Change (%)",
            marker_color=colors,
            opacity=0.3
        ),
        secondary_y=True,
    )
            
    fig.update_layout(**LAYOUT_DEFAULTS)
    fig.update_layout(
        title=f"🌍 {label}",
        height=350,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_yaxes(title_text="Value", secondary_y=False, **YAXIS_DEFAULTS)
    fig.update_yaxes(title_text="Change (%)", secondary_y=True, showgrid=False)
    
    return fig


def create_model_comparison_chart(comparison_df: pd.DataFrame) -> go.Figure:
    """
    Chart 13 — Model Comparison Bar Chart.
    """
    fig = go.Figure()
    
    if not comparison_df.empty and "Model" in comparison_df.columns:
        # Filter only successfully trained models
        df = comparison_df[comparison_df["Status"] == "✅ Trained"].copy()
        
        if not df.empty:
            # Convert percentage strings to floats
            for col in ["Accuracy", "F1", "ROC-AUC"]:
                if col in df.columns:
                    df[f"{col}_val"] = df[col].str.rstrip('%').astype(float)
            
            fig.add_trace(go.Bar(
                name="Accuracy",
                x=df["Model"],
                y=df["Accuracy_val"],
                marker_color=COLORS["blue"],
                text=df["Accuracy"],
                textposition='auto',
            ))
            
            fig.add_trace(go.Bar(
                name="F1 Score",
                x=df["Model"],
                y=df["F1_val"],
                marker_color=COLORS["purple"],
                text=df["F1"],
                textposition='auto',
            ))
            
            fig.add_trace(go.Bar(
                name="ROC-AUC",
                x=df["Model"],
                y=df["ROC-AUC_val"],
                marker_color=COLORS["orange"],
                text=df["ROC-AUC"],
                textposition='auto',
            ))
            
    fig.update_layout(**LAYOUT_DEFAULTS)
    fig.update_layout(
        yaxis={**YAXIS_DEFAULTS, "title": "Score (%)", "range": [0, 105]},
        title="🧪 Model Comparison (Ablation Analysis)",
        barmode='group',
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig
