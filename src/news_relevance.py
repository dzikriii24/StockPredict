"""
news_relevance.py — Evaluates the relevance of a news article to a specific stock.
"""

from typing import Dict
from src.company_metadata import get_company_metadata

def evaluate_relevance(title: str, description: str, ticker: str) -> Dict[str, str]:
    """
    Evaluates how relevant an article is to a given ticker.
    Returns a dictionary containing relevance scores.
    """
    text = f"{title} {description}".lower()
    meta = get_company_metadata(ticker)
    
    company_name = meta["company"].lower().replace(" pt", "").replace(" tbk", "").strip()
    base_ticker = ticker.replace(".JK", "").lower()
    sector = meta["sector"].lower()
    industry = meta["industry"].lower()
    keywords = [k.lower() for k in meta["keywords"]]
    
    # 1. Company Relevance
    company_hit = company_name in text or base_ticker in text
    
    # 2. Sector/Industry/Keyword Relevance
    keyword_hits = sum(1 for k in keywords if k in text)
    industry_hit = industry in text or sector in text
    
    # Combine scores
    if company_hit:
        overall = "HIGH"
        reason = f"Menyebutkan nama perusahaan atau ticker secara langsung."
    elif keyword_hits >= 2 or (keyword_hits == 1 and industry_hit):
        overall = "MEDIUM"
        reason = f"Berita ini membahas topik yang relevan dengan industri/sektor perusahaan ({industry})."
    elif keyword_hits == 1:
        overall = "LOW"
        reason = f"Menyinggung sedikit tentang topik yang mungkin berhubungan dengan perusahaan."
    else:
        overall = "IRRELEVANT"
        reason = f"Tidak ditemukan kaitan langsung dengan bisnis utama perusahaan."
        
    return {
        "overall_relevance": overall,
        "company_hit": "YES" if company_hit else "NO",
        "keyword_hits": keyword_hits,
        "reason": reason
    }
