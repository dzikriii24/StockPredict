"""
risk_analysis.py — Risk & Reward Analysis

Calculates position sizing, risk per trade,
potential profit/loss, and risk/reward ratio.
"""

import pandas as pd
import numpy as np
from typing import Optional


def calculate_position_size(
    capital: float,
    entry_price: float,
    stop_loss: float,
    risk_per_trade_pct: float = 2.0,
    lot_size: int = 100
) -> dict:
    """
    Calculate position size based on risk management rules.

    Position Size = (Capital × Risk%) / Risk per Share
    Risk per Share = Entry - Stop Loss

    Indonesian stocks are traded in lots of 100 shares.

    Args:
        capital: Total trading capital (Rp)
        entry_price: Entry price per share
        stop_loss: Stop loss price per share
        risk_per_trade_pct: Maximum risk per trade as % of capital (default: 2%)
        lot_size: Number of shares per lot (default: 100 for IDX)

    Returns:
        Dictionary with position sizing details
    """
    # Risk calculations
    risk_amount = capital * (risk_per_trade_pct / 100)  # Max Rp to risk
    risk_per_share = abs(entry_price - stop_loss)

    if risk_per_share <= 0:
        risk_per_share = entry_price * 0.02  # Fallback: 2% of entry

    # Position size
    max_shares = int(risk_amount / risk_per_share)

    # Round down to nearest lot (IDX trades in lots of 100)
    max_lots = max_shares // lot_size
    actual_shares = max_lots * lot_size

    # Cap by available capital
    max_affordable_shares = int(capital / entry_price)
    max_affordable_lots = max_affordable_shares // lot_size
    affordable_shares = max_affordable_lots * lot_size

    actual_shares = min(actual_shares, affordable_shares)
    actual_lots = actual_shares // lot_size

    # Total investment
    total_investment = actual_shares * entry_price

    return {
        "risk_amount": round(risk_amount, 0),
        "risk_per_share": round(risk_per_share, 0),
        "max_shares": actual_shares,
        "lots": actual_lots,
        "total_investment": round(total_investment, 0),
        "pct_of_capital": round((total_investment / capital) * 100, 1) if capital > 0 else 0,
    }


def calculate_transaction_analysis(
    capital: float,
    entry_price: float,
    target_price: float,
    stop_loss: float,
    risk_per_trade_pct: float = 2.0,
    transaction_cost_pct: float = 0.15
) -> dict:
    """
    Complete transaction analysis for a proposed trade.

    Args:
        capital: Total capital (Rp)
        entry_price: Entry price
        target_price: Target price
        stop_loss: Stop loss price
        risk_per_trade_pct: Risk per trade (% of capital)
        transaction_cost_pct: Transaction cost (% per trade, default: 0.15% for IDX)

    Returns:
        Dictionary with complete transaction analysis
    """
    # Position sizing
    position = calculate_position_size(
        capital, entry_price, stop_loss, risk_per_trade_pct
    )

    shares = position["max_shares"]

    if shares == 0:
        return {
            "position": position,
            "error": "Position size terlalu kecil. Capital tidak cukup atau risk terlalu kecil.",
            "potential_profit": 0,
            "potential_loss": 0,
            "risk_reward_ratio": 0,
        }

    # Potential Profit
    gross_profit = (target_price - entry_price) * shares
    buy_cost = entry_price * shares * (transaction_cost_pct / 100)
    sell_cost_profit = target_price * shares * (transaction_cost_pct / 100)
    net_profit = gross_profit - buy_cost - sell_cost_profit

    # Potential Loss
    gross_loss = (entry_price - stop_loss) * shares
    sell_cost_loss = stop_loss * shares * (transaction_cost_pct / 100)
    net_loss = gross_loss + buy_cost + sell_cost_loss

    # Risk/Reward Ratio
    if net_loss > 0:
        risk_reward = net_profit / net_loss
    else:
        risk_reward = 0

    # Return percentages
    profit_pct = (net_profit / position["total_investment"]) * 100 if position["total_investment"] > 0 else 0
    loss_pct = (net_loss / position["total_investment"]) * 100 if position["total_investment"] > 0 else 0

    return {
        "position": position,
        "entry_price": entry_price,
        "target_price": target_price,
        "stop_loss": stop_loss,
        "shares": shares,
        "lots": position["lots"],
        "total_investment": position["total_investment"],
        "transaction_cost_buy": round(buy_cost, 0),
        "potential_profit": round(net_profit, 0),
        "potential_profit_pct": round(profit_pct, 2),
        "potential_loss": round(net_loss, 0),
        "potential_loss_pct": round(loss_pct, 2),
        "risk_reward_ratio": round(risk_reward, 2),
        "risk_reward_display": f"1 : {risk_reward:.2f}",
    }


def get_risk_metrics(df: pd.DataFrame) -> dict:
    """
    Calculate various risk metrics from historical data.

    Args:
        df: DataFrame with Close and Daily_Return columns

    Returns:
        Dictionary with risk metrics
    """
    if "Daily_Return" not in df.columns:
        return {}

    returns = df["Daily_Return"].dropna() / 100  # Convert from percentage

    # Annualized metrics (252 trading days)
    annual_return = returns.mean() * 252
    annual_volatility = returns.std() * np.sqrt(252)

    # Sharpe Ratio (assuming risk-free rate of 5% for Indonesia)
    risk_free_rate = 0.05
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0

    # Maximum Drawdown
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_drawdown = drawdown.min()

    # Value at Risk (95%)
    var_95 = returns.quantile(0.05)

    # Sortino Ratio (downside deviation)
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() * np.sqrt(252)
    sortino_ratio = (annual_return - risk_free_rate) / downside_std if downside_std > 0 else 0

    return {
        "annual_return": round(annual_return * 100, 2),
        "annual_volatility": round(annual_volatility * 100, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "sortino_ratio": round(sortino_ratio, 2),
        "max_drawdown": round(max_drawdown * 100, 2),
        "var_95": round(var_95 * 100, 2),
        "avg_daily_return": round(returns.mean() * 100, 4),
        "best_day": round(returns.max() * 100, 2),
        "worst_day": round(returns.min() * 100, 2),
        "positive_days_pct": round((returns > 0).sum() / len(returns) * 100, 1),
    }


def get_model_limitations() -> list:
    """
    Return list of model limitations and disclaimers.

    Returns:
        List of limitation strings in Indonesian
    """
    return [
        "Historical performance tidak menjamin future performance.",
        "Harga saham dipengaruhi oleh faktor eksternal (berita, kebijakan, sentimen global) yang tidak ditangkap oleh model.",
        "Indikator teknikal bukan sinyal yang dijamin — banyak false signals yang mungkin terjadi.",
        "Prediksi machine learning mengandung ketidakpastian dan probabilitas, bukan kepastian.",
        "Transaction cost dan slippage dapat mempengaruhi actual returns secara signifikan.",
        "Model dapat terpengaruh oleh regime changes (perubahan kondisi pasar yang fundamental).",
        "Project ini dibuat untuk keperluan edukasi dan penelitian, BUKAN rekomendasi investasi personal.",
        "Selalu lakukan due diligence dan konsultasi dengan profesional sebelum membuat keputusan investasi.",
    ]
