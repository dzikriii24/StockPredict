"""
data_loader.py — Yahoo Finance Data Fetcher

Handles fetching historical OHLCV data from Yahoo Finance
for Indonesian stocks (suffix .JK).
Includes comprehensive IDX ticker database.
"""

import yfinance as yf
import pandas as pd
import os
from typing import Optional, List, Union, Dict
from datetime import datetime, timedelta


# ─── Comprehensive Indonesian Stock Tickers ──────────────────────
# Covers LQ45, IDX30, IDX80, and other popular stocks
TICKER_INFO: Dict[str, dict] = {
    # ── Banking ──
    "BBCA.JK": {"name": "Bank Central Asia", "sector": "Banking"},
    "BBRI.JK": {"name": "Bank Rakyat Indonesia", "sector": "Banking"},
    "BMRI.JK": {"name": "Bank Mandiri", "sector": "Banking"},
    "BBNI.JK": {"name": "Bank Negara Indonesia", "sector": "Banking"},
    "BRIS.JK": {"name": "Bank Syariah Indonesia", "sector": "Banking"},
    "BTPS.JK": {"name": "Bank BTPN Syariah", "sector": "Banking"},
    "MEGA.JK": {"name": "Bank Mega", "sector": "Banking"},
    "NISP.JK": {"name": "Bank OCBC NISP", "sector": "Banking"},
    "BNGA.JK": {"name": "Bank CIMB Niaga", "sector": "Banking"},
    "BDMN.JK": {"name": "Bank Danamon", "sector": "Banking"},
    "BJBR.JK": {"name": "Bank BJB", "sector": "Banking"},
    "ARTO.JK": {"name": "Bank Jago", "sector": "Banking"},
    "BJTM.JK": {"name": "Bank Jatim", "sector": "Banking"},
    # ── Telco & Tech ──
    "TLKM.JK": {"name": "Telkom Indonesia", "sector": "Telco & Tech"},
    "EXCL.JK": {"name": "XL Axiata", "sector": "Telco & Tech"},
    "ISAT.JK": {"name": "Indosat Ooredoo", "sector": "Telco & Tech"},
    "TOWR.JK": {"name": "Sarana Menara Nusantara", "sector": "Telco & Tech"},
    "TBIG.JK": {"name": "Tower Bersama", "sector": "Telco & Tech"},
    "GOTO.JK": {"name": "GoTo Gojek Tokopedia", "sector": "Telco & Tech"},
    "BUKA.JK": {"name": "Bukalapak", "sector": "Telco & Tech"},
    "EMTK.JK": {"name": "Elang Mahkota Teknologi", "sector": "Telco & Tech"},
    # ── Consumer Goods ──
    "ICBP.JK": {"name": "Indofood CBP", "sector": "Consumer"},
    "INDF.JK": {"name": "Indofood Sukses Makmur", "sector": "Consumer"},
    "UNVR.JK": {"name": "Unilever Indonesia", "sector": "Consumer"},
    "MYOR.JK": {"name": "Mayora Indah", "sector": "Consumer"},
    "KLBF.JK": {"name": "Kalbe Farma", "sector": "Consumer"},
    "HMSP.JK": {"name": "HM Sampoerna", "sector": "Consumer"},
    "GGRM.JK": {"name": "Gudang Garam", "sector": "Consumer"},
    "CPIN.JK": {"name": "Charoen Pokphand", "sector": "Consumer"},
    "JPFA.JK": {"name": "Japfa Comfeed", "sector": "Consumer"},
    "SIDO.JK": {"name": "Sido Muncul", "sector": "Consumer"},
    "TSPC.JK": {"name": "Tempo Scan Pacific", "sector": "Consumer"},
    "ULTJ.JK": {"name": "Ultra Jaya", "sector": "Consumer"},
    "ACES.JK": {"name": "Ace Hardware Indonesia", "sector": "Consumer"},
    "AMRT.JK": {"name": "Alfamart / Sumber Alfaria", "sector": "Consumer"},
    "LPPF.JK": {"name": "Matahari Department Store", "sector": "Consumer"},
    "MAPI.JK": {"name": "Mitra Adiperkasa", "sector": "Consumer"},
    # ── Automotive & Industrial ──
    "ASII.JK": {"name": "Astra International", "sector": "Automotive"},
    "AUTO.JK": {"name": "Astra Otoparts", "sector": "Automotive"},
    "SMSM.JK": {"name": "Selamat Sempurna", "sector": "Automotive"},
    "UNTR.JK": {"name": "United Tractors", "sector": "Industrial"},
    "ITMG.JK": {"name": "Indo Tambangraya Megah", "sector": "Mining"},
    # ── Mining & Energy ──
    "ANTM.JK": {"name": "Aneka Tambang", "sector": "Mining"},
    "INCO.JK": {"name": "Vale Indonesia", "sector": "Mining"},
    "PTBA.JK": {"name": "Bukit Asam", "sector": "Mining"},
    "ADRO.JK": {"name": "Adaro Energy", "sector": "Mining"},
    "MEDC.JK": {"name": "Medco Energi", "sector": "Energy"},
    "PGAS.JK": {"name": "Perusahaan Gas Negara", "sector": "Energy"},
    "AKRA.JK": {"name": "AKR Corporindo", "sector": "Energy"},
    "ESSA.JK": {"name": "Surya Esa Perkasa", "sector": "Energy"},
    "HRUM.JK": {"name": "Harum Energy", "sector": "Mining"},
    "TINS.JK": {"name": "Timah", "sector": "Mining"},
    "MDKA.JK": {"name": "Merdeka Copper Gold", "sector": "Mining"},
    "BSSR.JK": {"name": "Baramulti Suksessarana", "sector": "Mining"},
    # ── Property & Construction ──
    "BSDE.JK": {"name": "Bumi Serpong Damai", "sector": "Property"},
    "CTRA.JK": {"name": "Ciputra Development", "sector": "Property"},
    "SMRA.JK": {"name": "Summarecon Agung", "sector": "Property"},
    "PWON.JK": {"name": "Pakuwon Jati", "sector": "Property"},
    "WIKA.JK": {"name": "Wijaya Karya", "sector": "Construction"},
    "WSKT.JK": {"name": "Waskita Karya", "sector": "Construction"},
    "PTPP.JK": {"name": "PP (Persero)", "sector": "Construction"},
    "ADHI.JK": {"name": "Adhi Karya", "sector": "Construction"},
    "JSMR.JK": {"name": "Jasa Marga", "sector": "Infrastructure"},
    # ── Cement & Materials ──
    "SMGR.JK": {"name": "Semen Indonesia", "sector": "Cement"},
    "INTP.JK": {"name": "Indocement", "sector": "Cement"},
    "WSBP.JK": {"name": "Waskita Beton Precast", "sector": "Cement"},
    # ── Plantation & Agriculture ──
    "AALI.JK": {"name": "Astra Agro Lestari", "sector": "Plantation"},
    "LSIP.JK": {"name": "PP London Sumatra", "sector": "Plantation"},
    "DSNG.JK": {"name": "Dharma Satya Nusantara", "sector": "Plantation"},
    # ── Finance (Non-Bank) ──
    "BBTN.JK": {"name": "Bank Tabungan Negara", "sector": "Banking"},
    "PNLF.JK": {"name": "Panin Financial", "sector": "Finance"},
    "ADMF.JK": {"name": "Adira Dinamika Multi Finance", "sector": "Finance"},
    # ── Healthcare ──
    "HEAL.JK": {"name": "Medikaloka Hermina", "sector": "Healthcare"},
    "SILO.JK": {"name": "Siloam International Hospitals", "sector": "Healthcare"},
    # ── Media & Entertainment ──
    "SCMA.JK": {"name": "Surya Citra Media", "sector": "Media"},
    "MNCN.JK": {"name": "MNC Digital Entertainment", "sector": "Media"},
    # ── Chemicals & Packaging ──
    "BRPT.JK": {"name": "Barito Pacific", "sector": "Chemicals"},
    "TPIA.JK": {"name": "Chandra Asri Petrochemical", "sector": "Chemicals"},
    "INKP.JK": {"name": "Indah Kiat Pulp & Paper", "sector": "Pulp & Paper"},
    "TKIM.JK": {"name": "Pabrik Kertas Tjiwi Kimia", "sector": "Pulp & Paper"},
    # ── Transportation & Logistics ──
    "BIRD.JK": {"name": "Blue Bird", "sector": "Transportation"},
    "ASSA.JK": {"name": "Adi Sarana Armada", "sector": "Transportation"},
}

# Default tickers for quick analysis (top liquid stocks)
DEFAULT_TICKERS: List[str] = [
    "BBCA.JK", "BBRI.JK", "BMRI.JK", "BBNI.JK", "TLKM.JK",
    "ASII.JK", "ICBP.JK", "UNVR.JK", "ANTM.JK", "ADRO.JK",
    "GOTO.JK", "INDF.JK", "KLBF.JK", "PTBA.JK", "SMGR.JK",
]

# All available tickers
ALL_TICKERS: List[str] = sorted(TICKER_INFO.keys())

# Data cache directory
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def ensure_data_dir() -> None:
    """Create data directory if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)


def get_all_tickers() -> List[str]:
    """Return all available Indonesian stock tickers."""
    return ALL_TICKERS


def get_ticker_name(ticker: str) -> str:
    """Get company name for a ticker."""
    info = TICKER_INFO.get(ticker, {})
    return info.get("name", ticker.replace(".JK", ""))


def get_ticker_sector(ticker: str) -> str:
    """Get sector for a ticker."""
    info = TICKER_INFO.get(ticker, {})
    return info.get("sector", "Unknown")


def get_tickers_by_sector(sector: str) -> List[str]:
    """Get all tickers in a given sector."""
    return [t for t, info in TICKER_INFO.items() if info.get("sector") == sector]


def get_all_sectors() -> List[str]:
    """Get list of all unique sectors."""
    return sorted(set(info.get("sector", "Unknown") for info in TICKER_INFO.values()))


def fetch_stock_data(
    ticker: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = "1d",
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Fetch historical stock data from Yahoo Finance.

    Args:
        ticker: Stock ticker symbol (e.g., 'BBCA.JK')
        start_date: Start date in 'YYYY-MM-DD' format (default: 3 years ago)
        end_date: End date in 'YYYY-MM-DD' format (default: today)
        interval: Data interval ('1d', '1wk', '1mo')
        use_cache: Whether to use cached data

    Returns:
        DataFrame with OHLCV data

    Raises:
        ValueError: If ticker not found or data is empty
        ConnectionError: If unable to connect to Yahoo Finance
    """
    # Set default dates
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=3*365)).strftime("%Y-%m-%d")

    ensure_data_dir()

    # Check cache
    cache_file = os.path.join(
        DATA_DIR,
        f"{ticker.replace('.', '_')}_{start_date}_{end_date}_{interval}.csv"
    )

    is_intraday = interval in ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]
    is_today = end_date >= datetime.now().strftime("%Y-%m-%d")
    
    if use_cache and not is_intraday and not is_today and os.path.exists(cache_file):
        try:
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            if not df.empty:
                return df
        except Exception:
            pass  # If cache is corrupted, fetch fresh data

    # Fetch from Yahoo Finance
    try:
        stock = yf.Ticker(ticker)
        
        # yfinance's end date is exclusive, so we add 1 day to include the requested end_date
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            yf_end_date = end_dt.strftime("%Y-%m-%d")
        except ValueError:
            yf_end_date = end_date # Fallback if end_date is not in YYYY-MM-DD format
            
        df = stock.history(start=start_date, end=yf_end_date, interval=interval)
    except Exception as e:
        raise ConnectionError(
            f"Gagal mengambil data untuk {ticker}. "
            f"Periksa koneksi internet Anda. Error: {str(e)}"
        )

    # Validate data
    if df is None or df.empty:
        raise ValueError(
            f"Data tidak ditemukan untuk ticker '{ticker}'. "
            f"Pastikan ticker valid (contoh: BBCA.JK untuk saham Indonesia)."
        )

    # Clean column names — handle MultiIndex from newer yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Keep only OHLCV columns
    expected_cols = ["Open", "High", "Low", "Close", "Volume"]
    available_cols = [c for c in expected_cols if c in df.columns]

    if len(available_cols) < 4:  # At minimum need OHLC
        raise ValueError(
            f"Data untuk {ticker} tidak memiliki kolom yang diharapkan. "
            f"Kolom tersedia: {list(df.columns)}"
        )

    df = df[available_cols].copy()
    
    # Drop rows with NaN Close prices to prevent calculation errors
    if "Close" in df.columns:
        df = df.dropna(subset=["Close"])

    # Save to cache
    try:
        df.to_csv(cache_file)
    except Exception:
        pass  # Non-critical if cache save fails

    return df


def fetch_multiple_stocks(
    tickers: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    interval: str = "1d"
) -> dict:
    """
    Fetch data for multiple stock tickers.

    Args:
        tickers: List of ticker symbols
        start_date: Start date
        end_date: End date
        interval: Data interval

    Returns:
        Dictionary mapping ticker -> DataFrame
    """
    results = {}
    errors = {}

    for ticker in tickers:
        try:
            df = fetch_stock_data(ticker, start_date, end_date, interval, use_cache=True)
            results[ticker] = df
        except (ValueError, ConnectionError) as e:
            errors[ticker] = str(e)

    if errors:
        for ticker, error in errors.items():
            print(f"⚠️ Warning: {ticker} — {error}")

    return results


def get_stock_info(ticker: str) -> dict:
    """
    Get basic stock information.
    Uses local TICKER_INFO first, falls back to yfinance.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary with stock info
    """
    # Use local info first
    local_info = TICKER_INFO.get(ticker, {})
    if local_info:
        return {
            "ticker": ticker,
            "name": local_info.get("name", ticker),
            "sector": local_info.get("sector", "N/A"),
            "industry": local_info.get("sector", "N/A"),
            "currency": "IDR",
            "market_cap": None,
        }

    # Fallback to yfinance
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "ticker": ticker,
            "name": info.get("longName", info.get("shortName", ticker)),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "currency": info.get("currency", "IDR"),
            "market_cap": info.get("marketCap", None),
        }
    except Exception:
        return {
            "ticker": ticker,
            "name": ticker,
            "sector": "N/A",
            "industry": "N/A",
            "currency": "IDR",
            "market_cap": None,
        }
