"""
prediction.py — Machine Learning Prediction Module

Uses Random Forest Classifier to predict next-day price direction.
Implements chronological train/test split (NO random split for time series).

Supports model comparison:
- Model A: Technical Only
- Model B: Technical + News/Sentiment
- Model C: Technical + Macro
- Model D: Technical + News + Macro (All Features)
"""

import os
import time
import json
import joblib
import pandas as pd
import numpy as np
from typing import Tuple, Optional, List, Dict, Any
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report,
    roc_auc_score, mean_squared_error
)

from src.prediction_history import log_prediction


# Model storage directory
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")


def ensure_model_dir() -> None:
    """Create models directory if it doesn't exist."""
    os.makedirs(MODEL_DIR, exist_ok=True)


# ─── Feature Column Groups ──────────────────────────────────────
TECHNICAL_FEATURES = [
    "MA20", "MA50", "RSI", "MACD", "MACD_Signal",
    "BB_Upper", "BB_Lower", "Volume_Ratio",
    "Daily_Return", "Volatility"
]

NEWS_FEATURES = [
    "news_count", "average_sentiment", "Sentiment_MA3",
    "Sentiment_MA7", "sentiment_momentum"
]

MACRO_FEATURES = [
    "IHSG_Return", "USDIDR_Return", "Gold_Return",
    "Oil_Return", "Relative_Strength"
]

# Combined for backward compatibility
FEATURE_COLUMNS = TECHNICAL_FEATURES

# Model experiment configurations
MODEL_CONFIGS = {
    "A_Technical": {
        "name": "Technical Only",
        "features": TECHNICAL_FEATURES,
        "description": "Hanya menggunakan indikator teknikal (MA, RSI, MACD, BB, Volume, Volatility)",
    },
    "B_Tech_News": {
        "name": "Technical + News",
        "features": TECHNICAL_FEATURES + NEWS_FEATURES,
        "description": "Indikator teknikal + sentimen berita dan news momentum",
    },
    "C_Tech_Macro": {
        "name": "Technical + Macro",
        "features": TECHNICAL_FEATURES + MACRO_FEATURES,
        "description": "Indikator teknikal + data makroekonomi (IHSG, USD/IDR, Gold, Oil)",
    },
    "D_All_Features": {
        "name": "All Features",
        "features": TECHNICAL_FEATURES + NEWS_FEATURES + MACRO_FEATURES,
        "description": "Semua feature: teknikal + berita + makroekonomi",
    },
}


def prepare_ml_data(
    df: pd.DataFrame,
    feature_cols: List[str] = None,
    horizon: int = 1
) -> pd.DataFrame:
    """
    Prepare data for ML model by creating the target variable
    and selecting features.

    Target: 1 if future Close > current Close, else 0
    (No data leakage — target uses shift(-horizon))

    Args:
        df: DataFrame with all indicators calculated
        feature_cols: List of feature columns to use
        horizon: Prediction horizon in days (default: 1)

    Returns:
        DataFrame with features and target, NaN rows dropped
    """
    if feature_cols is None:
        feature_cols = TECHNICAL_FEATURES

    df = df.copy()

    # Target: future price direction and exact price
    df["Target"] = (df["Close"].shift(-horizon) > df["Close"]).astype(int)
    df["Target_Price"] = df["Close"].shift(-horizon)

    # Select only needed columns
    available_features = [c for c in feature_cols if c in df.columns]
    cols_needed = available_features + ["Target", "Target_Price", "Close"]
    cols_available = [c for c in cols_needed if c in df.columns]
    df = df[cols_available]

    # Drop NaN rows (from indicators and target shift)
    df = df.dropna()

    return df


def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.8
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data chronologically (NOT randomly) for time series.

    Args:
        df: Prepared ML DataFrame
        train_ratio: Proportion of data for training (default: 0.8)

    Returns:
        Tuple of (train_df, test_df)
    """
    split_idx = int(len(df) * train_ratio)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    return train_df, test_df


def _train_single_model(
    ml_data: pd.DataFrame,
    feature_cols: List[str],
    train_ratio: float = 0.8,
    n_estimators: int = 200,
    random_state: int = 42
) -> dict:
    """
    Train a single Random Forest model on prepared data.

    Args:
        ml_data: Prepared ML data
        feature_cols: Feature column names
        train_ratio: Split ratio
        n_estimators: Number of trees
        random_state: Random state

    Returns:
        Dictionary with model, metrics, predictions
    """
    available_features = [c for c in feature_cols if c in ml_data.columns]

    if len(available_features) < 2:
        return None

    # Chronological split
    train_df, test_df = chronological_split(ml_data, train_ratio)

    if len(train_df) < 50 or len(test_df) < 10:
        return None

    X_train = train_df[available_features].values
    y_train_class = train_df["Target"].values
    y_train_reg = train_df["Target_Price"].values
    
    X_test = test_df[available_features].values
    y_test_class = test_df["Target"].values
    y_test_reg = test_df["Target_Price"].values

    # Train Random Forest Classifier
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=random_state,
        n_jobs=-1
    )
    clf.fit(X_train, y_train_class)
    
    # Train Random Forest Regressor
    reg = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=random_state,
        n_jobs=-1
    )
    reg.fit(X_train, y_train_reg)

    # Predictions
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)
    y_pred_price = reg.predict(X_test)

    # Metrics
    try:
        roc_auc = roc_auc_score(y_test_class, y_prob[:, 1]) if y_prob.shape[1] > 1 else 0.5
    except (ValueError, IndexError):
        roc_auc = 0.5

    rmse = float(np.sqrt(mean_squared_error(y_test_reg, y_pred_price))) if len(y_test_reg) > 0 else 0.0

    metrics = {
        "accuracy": accuracy_score(y_test_class, y_pred),
        "precision": precision_score(y_test_class, y_pred, zero_division=0),
        "recall": recall_score(y_test_class, y_pred, zero_division=0),
        "f1_score": f1_score(y_test_class, y_pred, zero_division=0),
        "roc_auc": roc_auc,
        "rmse": rmse,
        "confusion_matrix": confusion_matrix(y_test_class, y_pred),
        "classification_report": classification_report(y_test_class, y_pred, output_dict=True),
    }

    # Feature importance
    feature_importance = dict(zip(available_features, clf.feature_importances_))

    # Build test results
    test_results = test_df.copy()
    test_results["Predicted"] = y_pred
    test_results["Predicted_Price"] = y_pred_price
    test_results["Prob_UP"] = y_prob[:, 1] if y_prob.shape[1] > 1 else y_prob[:, 0]
    test_results["Prob_DOWN"] = y_prob[:, 0] if y_prob.shape[1] > 1 else 1 - y_prob[:, 0]

    return {
        "model": {"classifier": clf, "regressor": reg},
        "metrics": metrics,
        "feature_importance": feature_importance,
        "feature_columns": available_features,
        "train_size": len(train_df),
        "test_size": len(test_df),
        "train_period": f"{train_df.index.min().strftime('%Y-%m-%d')} to {train_df.index.max().strftime('%Y-%m-%d')}",
        "test_period": f"{test_df.index.min().strftime('%Y-%m-%d')} to {test_df.index.max().strftime('%Y-%m-%d')}",
        "test_results": test_results,
    }


def train_model(
    df: pd.DataFrame,
    ticker: str = "default",
    train_ratio: float = 0.8,
    n_estimators: int = 200,
    random_state: int = 42,
    horizon: int = 1
) -> dict:
    """
    Train Random Forest Classifier on the prepared data.
    Uses the best available features (all if external data is available).

    Args:
        df: DataFrame with all indicators
        ticker: Ticker name for model saving
        train_ratio: Train/test split ratio
        n_estimators: Number of trees
        random_state: Random state
        horizon: Prediction horizon in days

    Returns:
        Dictionary with model, metrics, predictions, and split info
    """
    # Determine which features are available
    all_features = TECHNICAL_FEATURES + NEWS_FEATURES + MACRO_FEATURES
    available = [c for c in all_features if c in df.columns]

    if not available:
        available = TECHNICAL_FEATURES

    # Prepare ML data
    ml_data = prepare_ml_data(df, available, horizon)

    if len(ml_data) < 100:
        raise ValueError(
            f"Data terlalu sedikit untuk training ({len(ml_data)} rows). "
            f"Minimal 100 rows diperlukan."
        )

    result = _train_single_model(ml_data, available, train_ratio, n_estimators, random_state)

    if result is None:
        raise ValueError("Gagal melatih model. Periksa data dan features.")

    # Save model
    ensure_model_dir()
    model_path = os.path.join(MODEL_DIR, f"{ticker.replace('.', '_')}_model_{horizon}d.joblib")
    meta_path = os.path.join(MODEL_DIR, f"{ticker.replace('.', '_')}_model_{horizon}d.meta.json")
    
    joblib.dump(result["model"], model_path)
    
    # Save metadata (convert numpy types to python native for JSON)
    metrics_raw = result["metrics"]
    safe_metrics = {
        "accuracy": float(metrics_raw.get("accuracy", 0)),
        "precision": float(metrics_raw.get("precision", 0)),
        "recall": float(metrics_raw.get("recall", 0)),
        "f1_score": float(metrics_raw.get("f1_score", 0)),
        "roc_auc": float(metrics_raw.get("roc_auc", 0)),
        "rmse": float(metrics_raw.get("rmse", 0))
    }
    
    meta_data = {
        "metrics": safe_metrics,
        "feature_columns": result["feature_columns"]
    }
    with open(meta_path, 'w') as f:
        json.dump(meta_data, f)
        
    result["model_path"] = model_path

    return result


def train_model_comparison(
    df: pd.DataFrame,
    ticker: str = "default",
    train_ratio: float = 0.8,
    n_estimators: int = 200,
    random_state: int = 42
) -> Dict[str, dict]:
    """
    Train multiple models for comparison (ablation study).

    Models:
    - A: Technical Only
    - B: Technical + News
    - C: Technical + Macro
    - D: All Features

    All models use the SAME chronological split.

    Args:
        df: DataFrame with all features
        ticker: Ticker name
        train_ratio: Split ratio
        n_estimators: Trees per model
        random_state: Random state

    Returns:
        Dictionary mapping model_key -> result dict
    """
    comparison = {}

    for key, config in MODEL_CONFIGS.items():
        features = config["features"]
        available = [c for c in features if c in df.columns]

        if len(available) < 2:
            comparison[key] = {
                "name": config["name"],
                "description": config["description"],
                "error": f"Insufficient features ({len(available)} available)",
                "features_available": available,
            }
            continue

        ml_data = prepare_ml_data(df, available)

        if len(ml_data) < 100:
            comparison[key] = {
                "name": config["name"],
                "description": config["description"],
                "error": f"Insufficient data ({len(ml_data)} rows)",
                "features_available": available,
            }
            continue

        result = _train_single_model(ml_data, available, train_ratio, n_estimators, random_state)

        if result is None:
            comparison[key] = {
                "name": config["name"],
                "description": config["description"],
                "error": "Training failed",
                "features_available": available,
            }
        else:
            result["name"] = config["name"]
            result["description"] = config["description"]
            comparison[key] = result

    return comparison


def get_comparison_table(comparison: Dict[str, dict]) -> pd.DataFrame:
    """
    Build a comparison table from model comparison results.

    Args:
        comparison: Dictionary from train_model_comparison

    Returns:
        DataFrame with model comparison metrics
    """
    rows = []
    for key, result in comparison.items():
        if "error" in result:
            rows.append({
                "Model": result.get("name", key),
                "Features": len(result.get("features_available", [])),
                "Accuracy": "N/A",
                "Precision": "N/A",
                "Recall": "N/A",
                "F1": "N/A",
                "ROC-AUC": "N/A",
                "Status": f"⚠️ {result['error']}",
            })
        else:
            m = result["metrics"]
            rows.append({
                "Model": result.get("name", key),
                "Features": len(result.get("feature_columns", [])),
                "Accuracy": f"{m['accuracy']*100:.1f}%",
                "Precision": f"{m['precision']*100:.1f}%",
                "Recall": f"{m['recall']*100:.1f}%",
                "F1": f"{m['f1_score']*100:.1f}%",
                "ROC-AUC": f"{m.get('roc_auc', 0)*100:.1f}%",
                "Status": "✅ Trained",
            })

    return pd.DataFrame(rows)


def predict_latest(
    df: pd.DataFrame,
    model: dict, # Dictionary containing classifier and regressor
    feature_columns: list
) -> dict:
    """
    Make prediction for the latest data point.

    Args:
        df: Full DataFrame with indicators
        model: Dictionary with 'classifier' and 'regressor'
        feature_columns: List of feature column names

    Returns:
        Dictionary with prediction details
    """
    available_features = [c for c in feature_columns if c in df.columns]
    ml_data = df.dropna(subset=available_features)

    if ml_data.empty:
        return {
            "prediction": "N/A",
            "prob_up": 0.5,
            "prob_down": 0.5,
            "predicted_price": None,
            "current_price": None,
            "date": None,
        }

    latest = ml_data.iloc[-1]
    X_latest = latest[available_features].values.reshape(1, -1)

    # If backward compatibility (model is just a Classifier)
    if isinstance(model, RandomForestClassifier):
        clf = model
        reg = None
    else:
        clf = model["classifier"]
        reg = model.get("regressor")

    prediction = clf.predict(X_latest)[0]
    probabilities = clf.predict_proba(X_latest)[0]
    
    predicted_price = reg.predict(X_latest)[0] if reg else None

    prob_up = probabilities[1] if len(probabilities) > 1 else probabilities[0]
    prob_down = probabilities[0] if len(probabilities) > 1 else 1 - probabilities[0]

    current_price = float(latest["Close"])
            
    return {
        "prediction": "UP" if prediction == 1 else "DOWN",
        "prediction_value": int(prediction),
        "prob_up": float(prob_up),
        "prob_down": float(prob_down),
        "predicted_price": float(predicted_price) if predicted_price else None,
        "current_price": current_price,
        "date": latest.name.strftime("%Y-%m-%d %H:%M:%S") if hasattr(latest.name, "strftime") else str(latest.name),
    }


def load_model(ticker: str, horizon: int = 1) -> Optional[RandomForestClassifier]:
    """Load a saved model from disk."""
    model_path = os.path.join(MODEL_DIR, f"{ticker.replace('.', '_')}_model_{horizon}d.joblib")
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None

def train_and_predict(df: pd.DataFrame, ticker: str = "default", train_ratio: float = 0.8) -> dict:
    """
    Convenience wrapper to train multi-horizon models based on data interval
    and get predictions for the latest date.
    
    Dynamic Horizons based on interval suffix in ticker (e.g., BBCA.JK_1m)
    - 1m: 10, 20, 30, 40, 50, 60
    - 5m: 2, 4, 6, 8, 10, 12
    - 15m: 1, 2, 3, 4 (up to 1 hour)
    - 1h: 1, 2, 3, 4, 5, 6
    - 1d: 1, 5, 20
    """
    try:
        # Determine Horizons
        timeframe = ticker.split('_')[1] if '_' in ticker else "1d"
        base_ticker = ticker.split('_')[0]
        
        if timeframe == "1m":
            horizons = [10, 20, 30, 40, 50, 60]
        elif timeframe == "5m":
            horizons = [2, 4, 6, 8, 10, 12]
        elif timeframe == "15m":
            horizons = [1, 2, 3, 4]
        elif timeframe == "1h":
            horizons = [1, 2, 3, 4, 5, 6]
        else: # default 1d
            horizons = [1, 5, 20]
            
        results = {}
        predicted_path = []
        lower_bound = []
        upper_bound = []
        current_price = None
        first_h = horizons[0]
        
        for i, h in enumerate(horizons):
            model_path = os.path.join(MODEL_DIR, f"{ticker.replace('.', '_')}_model_{h}d_{int(train_ratio*100)}split.joblib")
            meta_path = os.path.join(MODEL_DIR, f"{ticker.replace('.', '_')}_model_{h}d_{int(train_ratio*100)}split.meta.json")
            
            is_cached = False
            if os.path.exists(model_path) and os.path.exists(meta_path):
                file_age = time.time() - os.path.getmtime(model_path)
                if file_age < 24 * 3600:
                    try:
                        model = joblib.load(model_path)
                        with open(meta_path, 'r') as f:
                            meta = json.load(f)
                        
                        res = {
                            "model": model,
                            "metrics": meta["metrics"],
                            "feature_columns": meta["feature_columns"],
                            "test_results": pd.DataFrame()
                        }
                        is_cached = True
                    except Exception:
                        pass
                        
            if not is_cached:
                res = train_model(df, ticker=f"{ticker}_{int(train_ratio*100)}split", horizon=h, train_ratio=train_ratio)
            
            pred_details = predict_latest(df, res["model"], res["feature_columns"])
            
            if current_price is None:
                current_price = pred_details["current_price"]
                
            # Build trajectory
            p_price = pred_details.get("predicted_price")
            rmse = res["metrics"].get("rmse", 0)
            
            if p_price:
                predicted_path.append(p_price)
                # Expand bound relative to RMSE and prediction time (multiplier 1.96 for ~95% confidence on residuals)
                # Ensure the bound widens appropriately if model becomes uncertain
                lower_bound.append(p_price - (rmse * 1.96))
                upper_bound.append(p_price + (rmse * 1.96))
            
            results[f"{h}d"] = {
                "prediction": pred_details["prediction"],
                "probability": max(pred_details["prob_up"], pred_details["prob_down"]),
                "predicted_price": p_price,
                "prob_up": pred_details["prob_up"],
                "prob_down": pred_details["prob_down"],
                "accuracy": res["metrics"]["accuracy"],
                "rmse": rmse,
                "test_results": res.get("test_results", pd.DataFrame()),
                "feature_columns": res["feature_columns"],
                "cached": is_cached
            }
            
        # Log prediction to database (logging the assembled path)
        if predicted_path:
            try:
                # Add back the first horizon into the dict for easy UI access
                results[f"{first_h}d"]["predicted_path"] = predicted_path
                results[f"{first_h}d"]["lower_bound"] = lower_bound
                results[f"{first_h}d"]["upper_bound"] = upper_bound
                
                log_prediction(
                    ticker=base_ticker,
                    timeframe=timeframe,
                    horizon_periods=first_h, # Base horizon representation
                    current_price=current_price,
                    predicted_prices=predicted_path,
                    direction_prediction=results[f"{first_h}d"]["prediction"],
                    model_version=f"RF_{len(horizons)}p_split{int(train_ratio*100)}"
                )
            except Exception as e:
                print(f"Failed to log prediction: {e}")
        
        # Fallbacks for backward compatibility
        legacy_1d = f"{horizons[0]}d"
        return {
            "status": "success",
            "horizons": results,
            "today_prediction": results[legacy_1d]["prediction"],
            "probability": results[legacy_1d]["probability"],
            "accuracy": results[legacy_1d]["accuracy"],
            "test_results": results[legacy_1d]["test_results"],
            "feature_columns": results[legacy_1d]["feature_columns"]
        }
    except Exception as e:
        print(f"Prediction error: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
