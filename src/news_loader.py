"""
news_loader.py — Context-Aware Financial News Fetcher

Fetches financial news from:
1. yfinance news (primary, free)
2. NewsAPI.org (optional, requires API key)

Maps news to stock tickers using context-aware keyword matching
from company_metadata.
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import warnings
warnings.filterwarnings("ignore")

from src.company_metadata import get_company_metadata

NEWS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "news")

def ensure_news_dir() -> None:
    os.makedirs(NEWS_DIR, exist_ok=True)

def _get_api_key() -> Optional[str]:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    return os.environ.get("NEWS_API_KEY")

def fetch_yfinance_news(ticker: str, max_items: int = 15) -> List[dict]:
    import yfinance as yf
    try:
        stock = yf.Ticker(ticker)
        raw_news = stock.news
        if not raw_news: return []

        news_list = []
        for item in raw_news[:max_items]:
            pub_date = None
            if "providerPublishTime" in item:
                pub_date = datetime.fromtimestamp(item["providerPublishTime"])
            elif "publishedAt" in item:
                try:
                    pub_date = datetime.fromisoformat(item["publishedAt"].replace("Z", "+00:00"))
                except:
                    pub_date = datetime.now()
            if pub_date is None: pub_date = datetime.now()

            title = item.get("title", item.get("headline", ""))
            if not title: continue

            news_list.append({
                "title": title,
                "description": item.get("summary", item.get("description", "")),
                "source": item.get("publisher", item.get("source", "Yahoo Finance")),
                "published_at": pub_date.strftime("%Y-%m-%d %H:%M:%S"),
                "date": pub_date.strftime("%Y-%m-%d"),
                "url": item.get("link", item.get("url", "")),
                "ticker": ticker,
                "search_query": "yfinance_direct"
            })
        return news_list
    except Exception as e:
        print(f"⚠️ Could not fetch yfinance news for {ticker}: {e}")
        return []

def fetch_newsapi_news(query: str, from_date: Optional[str] = None, max_items: int = 20) -> List[dict]:
    api_key = _get_api_key()
    if not api_key or api_key == "your_api_key_here" or not query:
        return []
    try:
        import requests
        if from_date is None:
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "from": from_date,
            "sortBy": "relevancy",
            "pageSize": min(max_items, 50),
            "apiKey": api_key,
            "language": "id"
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("status") != "ok": return []

        news_list = []
        for article in data.get("articles", []):
            title = article.get("title", "")
            if not title: continue

            pub_date = article.get("publishedAt", "")
            try:
                dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except:
                dt = datetime.now()

            news_list.append({
                "title": title,
                "description": article.get("description", "") or "",
                "source": article.get("source", {}).get("name", "Unknown"),
                "published_at": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "date": dt.strftime("%Y-%m-%d"),
                "url": article.get("url", ""),
                "ticker": "GENERAL",
                "search_query": query
            })
        return news_list
    except Exception as e:
        print(f"⚠️ NewsAPI error: {e}")
        return []

def _clean_news_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    df = df.copy()
    df = df[df["title"].notna() & (df["title"].str.strip() != "")]
    df = df.drop_duplicates(subset=["title"], keep="first")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=["date"])
    df = df.sort_values("date", ascending=False).reset_index(drop=True)
    return df

def get_contextual_news(ticker: str, use_cache: bool = True) -> pd.DataFrame:
    """
    Fetch news based on company metadata (Company, Sector, Industry, Keywords).
    """
    ensure_news_dir()
    cache_date = datetime.now().strftime("%Y-%m-%d")
    cache_file = os.path.join(NEWS_DIR, f"news_{ticker}_{cache_date}.json")

    if use_cache and os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if cached: return _clean_news_df(pd.DataFrame(cached))
        except: pass

    all_news = []
    meta = get_company_metadata(ticker)

    # 1. Fetch yfinance direct
    all_news.extend(fetch_yfinance_news(ticker))

    # 2. Build context queries
    company_name = meta["company"].replace(" PT", "").replace(" Tbk", "").strip()
    sector = meta["sector"]
    keywords = meta["keywords"][:5] # top 5 keywords
    
    # Query 1: Direct Company Name
    q_company = f'"{company_name}" OR "{ticker.replace(".JK", "")}"'
    
    # Query 2: Sector & Keywords (Broad)
    q_industry = " OR ".join([f'"{k}"' for k in keywords]) if keywords else ""
    
    # Fetch from NewsAPI
    all_news.extend(fetch_newsapi_news(q_company, max_items=20))
    if q_industry:
        # For industry, we only want to fetch generic news if it's highly relevant to avoid spam
        all_news.extend(fetch_newsapi_news(q_industry, max_items=15))

    if not all_news:
        return pd.DataFrame(columns=[
            "title", "description", "source", "published_at",
            "date", "url", "ticker", "search_query"
        ])

    df = _clean_news_df(pd.DataFrame(all_news))
    df["ticker"] = ticker # assign primary ticker for this context

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(df.to_dict("records"), f, ensure_ascii=False, default=str)
    except: pass

    return df

def get_news_status() -> dict:
    api_key = _get_api_key()
    return {
        "yfinance": True,
        "newsapi": bool(api_key and api_key != "your_api_key_here"),
        "api_key_set": bool(api_key and api_key != "your_api_key_here"),
    }
