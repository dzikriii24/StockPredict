import streamlit as st
import pandas as pd
import math
from src.ui.market_overview import fetch_market_snapshot, render_mini_analysis
from src.visualization import COLORS

def render_all_stocks():
    st.title(":material/inventory_2: Seluruh Saham")
    st.markdown("Daftar lengkap seluruh saham yang dipantau dalam sistem.")
    
    with st.spinner("Memuat data saham..."):
        df = fetch_market_snapshot()
        
    if df.empty:
        st.warning("Data tidak tersedia.")
        return
        
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        sector_filter = st.selectbox("Filter Berdasarkan Sektor", ["Semua"] + sorted(list(df["Sector"].unique())))
    with col2:
        trend_filter = st.selectbox("Filter Tren", ["Semua", "Naik (+)", "Turun (-)", "Tetap"])
        
    # Apply filters
    filtered_df = df.copy()
    if sector_filter != "Semua":
        filtered_df = filtered_df[filtered_df["Sector"] == sector_filter]
        
    if trend_filter == "Naik (+)":
        filtered_df = filtered_df[filtered_df["Change (%)"] > 0]
    elif trend_filter == "Turun (-)":
        filtered_df = filtered_df[filtered_df["Change (%)"] < 0]
    elif trend_filter == "Tetap":
        filtered_df = filtered_df[filtered_df["Change (%)"] == 0]
        
    # Format DataFrame for display
    display_df = filtered_df[["Ticker", "Company", "Sector", "Industry", "Price", "Change (%)", "Volume"]].copy()
    
    st.markdown("### :material/list_alt: Ringkasan Data")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Kode Saham", width="small"),
            "Company": st.column_config.TextColumn("Perusahaan"),
            "Sector": st.column_config.TextColumn("Sektor"),
            "Price": st.column_config.NumberColumn("Harga (Rp)", format="%.0f"),
            "Change (%)": st.column_config.NumberColumn("Perubahan (%)", format="%.2f%%"),
            "Volume": st.column_config.NumberColumn("Volume", format="%.0f"),
        }
    )
    
    st.markdown("---")
    st.markdown("### :material/query_stats: Analisis Visual & Prediksi")
    st.markdown("Karena memproses Machine Learning untuk seluruh saham membutuhkan waktu, data ditampilkan per 5 saham.")
    
    col_time, col_page = st.columns([1, 1])
    with col_time:
        interval_options = {"1d": "Harian", "1h": "1 Jam", "15m": "15 Menit", "5m": "5 Menit", "1m": "1 Menit"}
        selected_interval = st.selectbox("Periode Waktu", list(interval_options.keys()), format_func=lambda x: interval_options[x], index=0, key="all_stocks_timeframe")
    
    page_size = 5
    total_pages = max(1, math.ceil(len(filtered_df) / page_size))
    
    with col_page:
        page = st.number_input(f"Halaman (1 - {total_pages})", min_value=1, max_value=total_pages, value=1)
        
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    current_df = filtered_df.iloc[start_idx:end_idx]
    
    st.write(f"Menampilkan {start_idx + 1} - {min(end_idx, len(filtered_df))} dari {len(filtered_df)} saham.")
    
    for _, row in current_df.iterrows():
        ticker = row['Ticker']
        clean_ticker = ticker.replace('.JK', '')
        pct = row['Change (%)']
        prefix = "+" if pct > 0 else ""
        
        with st.expander(f"{clean_ticker} — {row['Company']} ({prefix}{pct}%)", expanded=True):
            render_mini_analysis(ticker, row['Company'], row['Price'], pct, interval=selected_interval, category="all_stocks")
