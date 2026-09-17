"""
prediction_history.py — Prediction History & Walk-Forward Validation

Stores AI predictions in a local SQLite database to track historical accuracy
without lookahead bias. Enables walk-forward validation and visually charting
past predictions against actual outcomes.
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any, List

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "predictions.db")

def _get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialize the prediction history table."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                prediction_timestamp TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                prediction_horizon INTEGER NOT NULL,
                current_price REAL,
                predicted_price_t1 REAL,
                predicted_price_t2 REAL,
                predicted_price_t3 REAL,
                predicted_price_t4 REAL,
                predicted_price_t5 REAL,
                actual_price_t1 REAL,
                actual_price_t2 REAL,
                actual_price_t3 REAL,
                actual_price_t4 REAL,
                actual_price_t5 REAL,
                direction_prediction TEXT,
                actual_direction TEXT,
                model_version TEXT
            )
        ''')
        conn.commit()

# Ensure DB is initialized on module load
init_db()

def log_prediction(
    ticker: str,
    timeframe: str,
    horizon_periods: int,
    current_price: float,
    predicted_prices: List[float],
    direction_prediction: str,
    model_version: str = "v1.0"
):
    """
    Log a new prediction to the database.
    predicted_prices should be a list of up to 5 future prices.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Pad or truncate predictions to exactly 5 elements
    preds = (predicted_prices + [None] * 5)[:5]
    
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO prediction_history (
                ticker, prediction_timestamp, timeframe, prediction_horizon,
                current_price, predicted_price_t1, predicted_price_t2,
                predicted_price_t3, predicted_price_t4, predicted_price_t5,
                direction_prediction, model_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticker, timestamp, timeframe, horizon_periods,
            current_price, preds[0], preds[1], preds[2], preds[3], preds[4],
            direction_prediction, model_version
        ))
        conn.commit()

def update_actuals(
    prediction_id: int,
    actual_prices: List[float]
):
    """
    Update a historical prediction with actual prices once they occur.
    """
    # Pad or truncate actuals to exactly 5 elements
    acts = (actual_prices + [None] * 5)[:5]
    
    with _get_connection() as conn:
        # First get the original current_price and predicted direction to calculate actual direction
        cursor = conn.cursor()
        cursor.execute('SELECT current_price, predicted_price_t5 FROM prediction_history WHERE id = ?', (prediction_id,))
        row = cursor.fetchone()
        
        actual_direction = None
        if row and row[0] is not None and acts[0] is not None: # Compare against t1 or t_horizon
            # We'll use the last available actual price to determine overall direction
            last_valid_actual = next((a for a in reversed(acts) if a is not None), None)
            if last_valid_actual is not None:
                actual_direction = "UP" if last_valid_actual > row[0] else "DOWN"

        cursor.execute('''
            UPDATE prediction_history SET
                actual_price_t1 = ?,
                actual_price_t2 = ?,
                actual_price_t3 = ?,
                actual_price_t4 = ?,
                actual_price_t5 = ?,
                actual_direction = ?
            WHERE id = ?
        ''', (acts[0], acts[1], acts[2], acts[3], acts[4], actual_direction, prediction_id))
        conn.commit()

def get_prediction_history(ticker: str = None, limit: int = 100) -> pd.DataFrame:
    """Fetch prediction history."""
    query = 'SELECT * FROM prediction_history'
    params = []
    
    if ticker:
        query += ' WHERE ticker = ?'
        params.append(ticker)
        
    query += ' ORDER BY prediction_timestamp DESC LIMIT ?'
    params.append(limit)
    
    with _get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df

def get_accuracy_metrics(ticker: str = None) -> Dict[str, Any]:
    """Calculate walk-forward accuracy metrics."""
    df = get_prediction_history(ticker, limit=1000)
    
    # Filter rows where actual_direction is known
    completed = df.dropna(subset=['actual_direction']).copy()
    
    if completed.empty:
        return {
            "directional_accuracy": 0.0,
            "correct_count": 0,
            "wrong_count": 0,
            "total_completed": 0,
            "mae_t1": 0.0,
            "rmse_t1": 0.0
        }
        
    # Calculate Directional Accuracy
    correct = (completed['direction_prediction'] == completed['actual_direction']).sum()
    total = len(completed)
    accuracy = correct / total if total > 0 else 0.0
    
    # Calculate MAE for T1
    completed['error_t1'] = completed['predicted_price_t1'] - completed['actual_price_t1']
    mae_t1 = completed['error_t1'].abs().mean()
    rmse_t1 = (completed['error_t1'] ** 2).mean() ** 0.5
    
    return {
        "directional_accuracy": accuracy,
        "correct_count": int(correct),
        "wrong_count": int(total - correct),
        "total_completed": int(total),
        "mae_t1": float(mae_t1) if pd.notna(mae_t1) else 0.0,
        "rmse_t1": float(rmse_t1) if pd.notna(rmse_t1) else 0.0
    }
