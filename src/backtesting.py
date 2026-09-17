"""
backtesting.py — Historical Backtesting Engine

Simulates trading based on generated signals,
calculates performance metrics, and compares with Buy & Hold.
"""

import pandas as pd
import numpy as np
from typing import Optional


def run_backtest(
    df: pd.DataFrame,
    initial_capital: float = 10_000_000,
    transaction_cost_pct: float = 0.15,
    target_pct: float = 5.0,
    stop_loss_pct: float = 3.0,
    lot_size: int = 100
) -> dict:
    """
    Run historical backtesting on signal data.

    Simulates trades:
    - Enter on BUY signal
    - Exit on SELL signal, target hit, or stop loss hit
    - Track equity, trades, and performance

    Args:
        df: DataFrame with 'Signal', 'Close', 'High', 'Low' columns
        initial_capital: Starting capital (default: Rp10,000,000)
        transaction_cost_pct: Cost per trade in % (default: 0.15%)
        target_pct: Target profit % per trade (default: 5%)
        stop_loss_pct: Stop loss % per trade (default: 3%)
        lot_size: IDX lot size (default: 100)

    Returns:
        Dictionary with backtesting results
    """
    df = df.copy()

    capital = initial_capital
    position = 0  # Number of shares held
    entry_price = 0
    trades = []
    equity_curve = []

    for i in range(len(df)):
        row = df.iloc[i]
        current_price = row["Close"]
        signal = row.get("Signal", "HOLD")
        date = df.index[i]

        # Check exit conditions if in position
        if position > 0:
            # Calculate current P&L
            current_value = position * current_price
            target_price = entry_price * (1 + target_pct / 100)
            sl_price = entry_price * (1 - stop_loss_pct / 100)

            exit_reason = None

            # Check target hit (use High for intraday target)
            if row.get("High", current_price) >= target_price:
                exit_reason = "Target Hit"
                exit_price = target_price

            # Check stop loss hit (use Low for intraday SL)
            elif row.get("Low", current_price) <= sl_price:
                exit_reason = "Stop Loss"
                exit_price = sl_price

            # Check SELL signal
            elif signal == "SELL":
                exit_reason = "Sell Signal"
                exit_price = current_price

            if exit_reason:
                # Execute exit
                sell_cost = exit_price * position * (transaction_cost_pct / 100)
                proceeds = exit_price * position - sell_cost
                profit = proceeds - (entry_price * position + entry_price * position * (transaction_cost_pct / 100))

                trades.append({
                    "entry_date": entry_date,
                    "exit_date": date,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "shares": position,
                    "profit": profit,
                    "profit_pct": (exit_price / entry_price - 1) * 100,
                    "exit_reason": exit_reason,
                })

                capital += proceeds
                position = 0
                entry_price = 0

        # Check entry conditions
        if position == 0 and signal == "BUY":
            # Calculate position size (use 90% of capital max)
            max_investment = capital * 0.9
            max_shares = int(max_investment / current_price)
            lots = max_shares // lot_size
            shares_to_buy = lots * lot_size

            if shares_to_buy > 0:
                buy_cost = current_price * shares_to_buy * (transaction_cost_pct / 100)
                total_cost = current_price * shares_to_buy + buy_cost

                if total_cost <= capital:
                    capital -= total_cost
                    position = shares_to_buy
                    entry_price = current_price
                    entry_date = date

        # Record equity
        portfolio_value = capital + (position * current_price)
        equity_curve.append({
            "date": date,
            "equity": portfolio_value,
            "capital": capital,
            "position_value": position * current_price,
            "in_position": position > 0,
        })

    # Close any remaining position
    if position > 0:
        final_price = df["Close"].iloc[-1]
        sell_cost = final_price * position * (transaction_cost_pct / 100)
        proceeds = final_price * position - sell_cost
        profit = proceeds - (entry_price * position + entry_price * position * (transaction_cost_pct / 100))

        trades.append({
            "entry_date": entry_date,
            "exit_date": df.index[-1],
            "entry_price": entry_price,
            "exit_price": final_price,
            "shares": position,
            "profit": profit,
            "profit_pct": (final_price / entry_price - 1) * 100,
            "exit_reason": "End of Period",
        })
        capital += proceeds
        position = 0

    # Build equity DataFrame
    equity_df = pd.DataFrame(equity_curve)
    if not equity_df.empty:
        equity_df.set_index("date", inplace=True)

    # Build trades DataFrame
    trades_df = pd.DataFrame(trades) if trades else pd.DataFrame()

    # Calculate metrics
    metrics = calculate_backtest_metrics(
        initial_capital, capital, trades_df, equity_df
    )

    # Buy & Hold comparison
    buy_hold = calculate_buy_hold(df, initial_capital, transaction_cost_pct, lot_size)

    return {
        "metrics": metrics,
        "trades": trades_df,
        "equity_curve": equity_df,
        "buy_hold": buy_hold,
        "final_capital": capital,
    }


def calculate_backtest_metrics(
    initial_capital: float,
    final_capital: float,
    trades_df: pd.DataFrame,
    equity_df: pd.DataFrame
) -> dict:
    """
    Calculate comprehensive backtesting metrics.

    Args:
        initial_capital: Starting capital
        final_capital: Ending capital
        trades_df: DataFrame of executed trades
        equity_df: Equity curve DataFrame

    Returns:
        Dictionary with performance metrics
    """
    total_return = ((final_capital / initial_capital) - 1) * 100

    if trades_df.empty:
        return {
            "initial_capital": initial_capital,
            "final_capital": round(final_capital, 0),
            "total_return": round(total_return, 2),
            "num_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "avg_profit": 0,
            "avg_loss": 0,
            "max_drawdown": 0,
            "profit_factor": 0,
        }

    # Trade statistics
    winning = trades_df[trades_df["profit"] > 0]
    losing = trades_df[trades_df["profit"] <= 0]

    num_trades = len(trades_df)
    win_count = len(winning)
    loss_count = len(losing)
    win_rate = (win_count / num_trades) * 100 if num_trades > 0 else 0

    avg_profit = winning["profit"].mean() if not winning.empty else 0
    avg_loss = losing["profit"].mean() if not losing.empty else 0

    total_profit = winning["profit"].sum() if not winning.empty else 0
    total_loss = abs(losing["profit"].sum()) if not losing.empty else 0
    profit_factor = total_profit / total_loss if total_loss > 0 else float("inf")

    # Maximum Drawdown
    max_drawdown = 0
    if not equity_df.empty and "equity" in equity_df.columns:
        equity_series = equity_df["equity"]
        rolling_max = equity_series.cummax()
        drawdown = (equity_series - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()

    return {
        "initial_capital": initial_capital,
        "final_capital": round(final_capital, 0),
        "total_return": round(total_return, 2),
        "num_trades": num_trades,
        "winning_trades": win_count,
        "losing_trades": loss_count,
        "win_rate": round(win_rate, 1),
        "avg_profit": round(avg_profit, 0),
        "avg_loss": round(avg_loss, 0),
        "max_drawdown": round(max_drawdown, 2),
        "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else "∞",
        "largest_win": round(winning["profit"].max(), 0) if not winning.empty else 0,
        "largest_loss": round(losing["profit"].min(), 0) if not losing.empty else 0,
    }


def calculate_buy_hold(
    df: pd.DataFrame,
    initial_capital: float,
    transaction_cost_pct: float = 0.15,
    lot_size: int = 100
) -> dict:
    """
    Calculate Buy & Hold strategy performance for comparison.

    Args:
        df: DataFrame with Close price
        initial_capital: Starting capital
        transaction_cost_pct: Transaction cost %
        lot_size: Lot size

    Returns:
        Dictionary with B&H performance and equity curve
    """
    if df.empty:
        return {"final_capital": initial_capital, "total_return": 0, "equity_curve": pd.DataFrame()}

    first_price = df["Close"].iloc[0]
    last_price = df["Close"].iloc[-1]

    # Buy at first price
    max_shares = int((initial_capital * 0.99) / first_price)  # 1% for costs
    lots = max_shares // lot_size
    shares = lots * lot_size

    if shares == 0:
        return {"final_capital": initial_capital, "total_return": 0, "equity_curve": pd.DataFrame()}

    buy_cost = first_price * shares * (transaction_cost_pct / 100)
    cash_remaining = initial_capital - (first_price * shares + buy_cost)

    # Sell at last price
    sell_cost = last_price * shares * (transaction_cost_pct / 100)
    final_capital = last_price * shares - sell_cost + cash_remaining

    total_return = ((final_capital / initial_capital) - 1) * 100

    # Build equity curve
    equity_data = []
    for i in range(len(df)):
        date = df.index[i]
        price = df["Close"].iloc[i]
        equity = cash_remaining + (shares * price)
        equity_data.append({"date": date, "equity": equity})

    equity_df = pd.DataFrame(equity_data)
    if not equity_df.empty:
        equity_df.set_index("date", inplace=True)

    # Max drawdown
    max_dd = 0
    if not equity_df.empty:
        eq = equity_df["equity"]
        rm = eq.cummax()
        dd = (eq - rm) / rm * 100
        max_dd = dd.min()

    return {
        "initial_capital": initial_capital,
        "final_capital": round(final_capital, 0),
        "total_return": round(total_return, 2),
        "shares": shares,
        "entry_price": first_price,
        "exit_price": last_price,
        "max_drawdown": round(max_dd, 2),
        "equity_curve": equity_df,
    }
