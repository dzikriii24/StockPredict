import json
import os
from typing import Dict, List, Optional
from src.data_loader import TICKER_INFO

METADATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "metadata.json")

# Default mapping for sectors to provide industry and generic keywords
SECTOR_MAPPING = {
    "Banking": {
        "industry": "Financials",
        "keywords": ["banking", "bank", "finance", "kredit", "suku bunga", "interest rate", "loan", "laba", "OJK", "BI", "Bank Indonesia"]
    },
    "Telco & Tech": {
        "industry": "Technology & Telecommunications",
        "keywords": ["tech", "telekomunikasi", "internet", "data", "digital", "startup", "ecommerce", "aplikasi", "5G", "broadband"]
    },
    "Consumer": {
        "industry": "Consumer Goods",
        "keywords": ["consumer", "retail", "fmcg", "makanan", "minuman", "daya beli", "inflasi", "konsumsi", "sales", "penjualan"]
    },
    "Agriculture": {
        "industry": "Plantation",
        "keywords": ["agriculture", "plantation", "palm oil", "cpo", "kelapa sawit", "pertanian", "cuaca", "el nino", "drought", "karhutla", "wildfire", "export"]
    },
    "Energy & Mining": {
        "industry": "Energy & Resources",
        "keywords": ["mining", "energy", "coal", "batu bara", "oil", "gas", "minyak", "tambang", "komoditas", "commodity", "export", "harga acuan"]
    },
    "Infrastructure & Property": {
        "industry": "Infrastructure",
        "keywords": ["infrastructure", "property", "konstruksi", "pembangunan", "real estate", "semen", "jalan tol", "proyek", "ikn"]
    },
    "Miscellaneous": {
        "industry": "Diversified",
        "keywords": ["conglomerate", "diversified", "otomotif", "holding", "investasi", "bisnis"]
    }
}

class CompanyMetadata:
    def __init__(self):
        self.metadata = {}
        self._load_or_generate_metadata()
        
    def _load_or_generate_metadata(self):
        # Create data dir if not exists
        os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
        
        if os.path.exists(METADATA_FILE):
            try:
                with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                return
            except Exception as e:
                print(f"Failed to load metadata.json: {e}. Generating default.")
                
        # Generate from TICKER_INFO
        for ticker, info in TICKER_INFO.items():
            sector = info.get("sector", "Miscellaneous")
            mapping = SECTOR_MAPPING.get(sector, SECTOR_MAPPING["Miscellaneous"])
            
            self.metadata[ticker] = {
                "ticker": ticker,
                "company": info.get("name", ticker),
                "sector": sector,
                "industry": mapping["industry"],
                "keywords": [info.get("name", "")] + mapping["keywords"]
            }
            
            # Specific additions for known stocks (e.g. AALI)
            if ticker == "AALI.JK":
                self.metadata[ticker]["keywords"].extend(["astra agro lestari", "kebakaran", "hutan", "lahan", "sawit", "crude palm oil"])
            elif ticker == "GOTO.JK":
                self.metadata[ticker]["keywords"].extend(["gojek", "tokopedia", "goto", "startup", "rugi bersih", "profitabilitas"])
            elif ticker == "BBCA.JK":
                self.metadata[ticker]["keywords"].extend(["bca", "bank central asia", "kredit", "bunga"])
                
        # Save to file
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=4)
            
    def get_metadata(self, ticker: str) -> Optional[dict]:
        """Get metadata for a specific ticker."""
        # Handle cases where user passes without .JK
        if not ticker.endswith('.JK'):
            ticker += '.JK'
        return self.metadata.get(ticker)
        
    def get_all_tickers(self) -> List[str]:
        return list(self.metadata.keys())
        
    def get_sectors(self) -> List[str]:
        return list(set(data["sector"] for data in self.metadata.values()))
        
    def get_tickers_by_sector(self, sector: str) -> List[str]:
        return [t for t, d in self.metadata.items() if d["sector"] == sector]

# Global instance
metadata_manager = CompanyMetadata()

def get_company_metadata(ticker: str) -> dict:
    meta = metadata_manager.get_metadata(ticker)
    if not meta:
        # Fallback for unknown tickers
        return {
            "ticker": ticker,
            "company": ticker.replace(".JK", ""),
            "sector": "Unknown",
            "industry": "Unknown",
            "keywords": [ticker.replace(".JK", "")]
        }
    return meta
