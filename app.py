"""
app.py — Stock Intelligence & Trading Analysis System v3.0

Main entry point. Uses a Sidebar Navigation system to switch between
different analytical modules cleanly.
"""

import streamlit as st
import warnings
warnings.filterwarnings("ignore")

# ─── Page Config ─────────────────────────────────────────────────
st.set_page_config(
    page_title="StockPredict",
    page_icon=":material/analytics:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Clean Aesthetics CSS ────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #0e1117; /* Sleek dark background */
        color: #c9d1d9;
    }
    
    /* Clean Cards */
    .kpi-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: left;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 1rem;
    }
    .kpi-label {
        color: #8b949e;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    }
    .kpi-green { color: #2ea043; }
    .kpi-red { color: #f85149; }
    
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-weight: 600;
    }
    
    /* Remove messy gradients and stick to solid clean colors */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)

# ─── Imports UI Modules ──────────────────────────────────────────
from src.ui.market_overview import render_market_overview
from src.ui.all_stocks import render_all_stocks
from src.ui.sector_map import render_sector_map
from src.ui.stock_analysis import render_stock_analysis
from src.ui.presentation_mode import render_presentation_mode
from src.ui.scanner_ui import render_scanner_ui
from src.company_metadata import metadata_manager

# ─── Sidebar Navigation ──────────────────────────────────────────
def main():
    with st.sidebar:
        st.title(":material/monitoring: StockPredict")
        st.markdown("Sistem Analisis Saham Profesional")
        st.markdown("---")
        
        from streamlit_option_menu import option_menu
        
        # Navigation Sections using option_menu
        nav_section = option_menu(
            menu_title=None,
            options=[
                "Live Market Center",
                "Daftar Semua Saham",
                "Peta Sektor Industri",
                "Pemindai Jangka Pendek",
                "Analisis Saham Mendalam",
                "Mode Presentasi"
            ],
            icons=["speedometer2", "list-task", "map", "radar", "graph-up-arrow", "easel"],
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#c9d1d9", "font-size": "16px"}, 
                "nav-link": {"font-size": "14px", "text-align": "left", "margin":"0px", "color": "#c9d1d9", "--hover-color": "#21262d"},
                "nav-link-selected": {"background-color": "#2ea043", "color": "#ffffff", "font-weight": "600"},
            }
        )
        
        st.markdown("---")
        
        # Global Ticker Selection (only show when needed)
        selected_ticker = None
        if nav_section in ["Analisis Saham Mendalam", "Mode Presentasi"]:
            tickers = sorted(metadata_manager.get_all_tickers())
            # Default to BBCA.JK if exists, else first one
            default_index = tickers.index("BBCA.JK") if "BBCA.JK" in tickers else 0
            selected_ticker = st.selectbox("Pilih Saham", tickers, index=default_index)
            
        st.caption("© 2026 StockPredict")
        st.caption("Created by Dzikri, Fadli, Daffa, Informatics Engineering 23")
    
    # ─── Routing ────────────────────────────────────────────────────
    if nav_section == "Live Market Center":
        render_market_overview()
    elif nav_section == "Daftar Semua Saham":
        render_all_stocks()
    elif nav_section == "Peta Sektor Industri":
        render_sector_map()
    elif nav_section == "Pemindai Jangka Pendek":
        render_scanner_ui()
    elif nav_section == "Analisis Saham Mendalam":
        render_stock_analysis(selected_ticker)
    elif nav_section == "Mode Presentasi":
        render_presentation_mode(selected_ticker)

if __name__ == "__main__":
    main()
