import streamlit as st
import pandas as pd
import plotly.express as px
from src.ui.market_overview import fetch_market_snapshot

def render_sector_map():
    st.title(":material/map: Peta Sektor Industri")
    st.markdown("Peta kondisi per sektor industri berdasarkan rata-rata performa harian.")
    
    with st.spinner("Memproses data sektor..."):
        df = fetch_market_snapshot()
        
    if df.empty:
        st.warning("Data tidak tersedia.")
        return
        
    # Aggregate by sector
    sector_agg = df.groupby("Sector").agg(
        num_stocks=("Ticker", "count"),
        avg_change=("Change (%)", "mean"),
        total_volume=("Volume", "sum")
    ).reset_index()
    
    # Render heatmap (treemap)
    fig = px.treemap(
        sector_agg, 
        path=["Sector"], 
        values="num_stocks",
        color="avg_change",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        custom_data=["avg_change", "total_volume"]
    )
    
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Stocks: %{value}<br>Avg Return: %{customdata[0]:.2f}%<br>Volume: %{customdata[1]:,.0f}"
    )
    
    fig.update_layout(
        margin=dict(t=30, l=10, r=10, b=10),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed sector list
    st.markdown("### :material/list: Detail Sektor")
    
    # Display as nice columns
    sectors = sector_agg.sort_values("avg_change", ascending=False)
    
    for _, row in sectors.iterrows():
        color = ":material/trending_up:" if row['avg_change'] > 0 else ":material/trending_down:" if row['avg_change'] < 0 else ":material/trending_flat:"
        with st.expander(f"{color} {row['Sector']} ({row['avg_change']:+.2f}%) — {row['num_stocks']} saham"):
            sector_stocks = df[df["Sector"] == row["Sector"]].sort_values("Change (%)", ascending=False)
            st.dataframe(
                sector_stocks[["Ticker", "Company", "Price", "Change (%)"]],
                use_container_width=True,
                hide_index=True
            )
