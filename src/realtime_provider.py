"""
realtime_provider.py — Market Data Provider Abstraction

Handles real-time and delayed data streaming/polling.
Provides a unified interface for data retrieval, enabling easy swaps between
delayed Yahoo Finance data and premium real-time data providers.
"""

from abc import ABC, abstractmethod
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import asyncio
from typing import Dict, Any, Optional

class MarketDataProvider(ABC):
    """Abstract base class for all market data providers."""
    
    @abstractmethod
    def get_provider_name(self) -> str:
        pass
        
    @abstractmethod
    def get_market_status(self, ticker: str) -> Dict[str, Any]:
        """Return market status: OPEN/CLOSED and data freshness (REAL-TIME/DELAYED)."""
        pass
        
    @abstractmethod
    def get_historical_data(self, ticker: str, start: str, end: str, interval: str) -> pd.DataFrame:
        pass
        
    @abstractmethod
    def get_quote(self, ticker: str) -> Dict[str, Any]:
        """Get latest real-time or delayed quote."""
        pass


class YahooDataProvider(MarketDataProvider):
    """
    Yahoo Finance implementation.
    Note: IDX (.JK) is always delayed ~15 mins on Yahoo Finance.
    US tickers are often real-time.
    """
    
    def get_provider_name(self) -> str:
        return "Yahoo Finance"
        
    def _is_idx(self, ticker: str) -> bool:
        return ticker.endswith(".JK")
        
    def _is_market_open(self, ticker: str) -> bool:
        # Simplistic market open check for IDX (WIB: 09:00 - 16:00, Mon-Fri)
        now = datetime.now()
        if self._is_idx(ticker):
            # Assumes local server time is WIB (UTC+7) or adjust accordingly.
            # For robustness, we check the last trade time if possible.
            # But roughly:
            weekday = now.weekday()
            hour = now.hour
            minute = now.minute
            
            if weekday > 4: # Weekend
                return False
                
            time_val = hour + minute / 60.0
            if 9.0 <= time_val <= 16.0:
                return True
            return False
        else:
            # Assume US market roughly 9:30 AM - 4:00 PM EST. 
            # This is a simplification.
            return True
        
    def get_market_status(self, ticker: str) -> Dict[str, Any]:
        is_open = self._is_market_open(ticker)
        is_idx = self._is_idx(ticker)
        
        status = {
            "provider": self.get_provider_name(),
            "market_status": "OPEN" if is_open else "CLOSED",
            "data_status": "DELAYED ~15 MIN" if is_idx else "REAL-TIME",
            "last_update": datetime.now().strftime("%H:%M:%S WIB"),
            "update_type": "Polling"
        }
        return status
        
    def get_historical_data(self, ticker: str, start: str, end: str, interval: str) -> pd.DataFrame:
        try:
            stock = yf.Ticker(ticker)
            # YF end date is exclusive, add 1 day
            end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
            yf_end = end_dt.strftime("%Y-%m-%d")
            
            df = stock.history(start=start, end=yf_end, interval=interval)
            
            if df.empty:
                return df
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            expected = ["Open", "High", "Low", "Close", "Volume"]
            avail = [c for c in expected if c in df.columns]
            
            df = df[avail].copy()
            if "Close" in df.columns:
                df = df.dropna(subset=["Close"])
                
            return df
            
        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return pd.DataFrame()
            
    def get_quote(self, ticker: str) -> Dict[str, Any]:
        try:
            stock = yf.Ticker(ticker)
            # Use fastinfo or fast history for latest quote
            info = stock.fast_info
            
            return {
                "price": info.last_price,
                "volume": info.last_volume,
                "timestamp": datetime.now(), # Approximate
            }
        except Exception:
            # Fallback to history
            try:
                df = stock.history(period="1d", interval="1m")
                if not df.empty:
                    last = df.iloc[-1]
                    return {
                        "price": float(last["Close"]),
                        "volume": int(last["Volume"]),
                        "timestamp": df.index[-1]
                    }
            except Exception:
                pass
            
            return {"price": None, "volume": None, "timestamp": None}

# Global Provider Instance
market_provider = YahooDataProvider()
