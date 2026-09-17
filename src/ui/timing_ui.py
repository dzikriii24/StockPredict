import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.historical_timing import generate_entry_exit_matrix, analyze_opening_range

def render_timing_summary(cand: dict):
    """
    Renders the summary of historical timing for the scanner UI.
    """
    timing = cand.get("Historical_Timing", {})
    if not timing or not timing.get("available"):
        st.info("Data historis intraday tidak mencukupi untuk analisis waktu eksekusi.")
        return
        
    st.markdown("**:material/schedule: ANALISIS WAKTU TRANSAKSI HISTORIS**")
    
    # Context message
    context = timing.get("context", {})
    if context.get("is_top_window"):
        st.success(context.get("message", ""))
    else:
        st.info(context.get("message", "Data historis diproses."))
        
    st.markdown("**Waktu Transaksi Paling Menguntungkan**")
    top_windows = timing.get("top_windows", [])
    
    if not top_windows:
        st.write("Belum ada data window yang signifikan.")
        return
        
    for i, w in enumerate(top_windows):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
        c1.markdown(f"**{w['time']}**")
        c2.write(f"Win: {w['win_rate']}%")
        c3.write(f"Med: {w['median_return']}%")
        c4.caption(f"Obs: {w['observations']}")
        
    st.caption(f"Analisis berdasarkan {timing.get('trading_days', 0)} hari trading terakhir.")

def render_full_timing_analysis(cand: dict, df_raw: pd.DataFrame):
    """
    Renders the detailed charts and matrices for Historical Market Timing.
    """
    timing = cand.get("Historical_Timing", {})
    if not timing or not timing.get("available"):
        st.error("Data historis intraday tidak tersedia untuk timeframe ini.")
        st.info("Silakan pilih mode Scalping atau Intraday dengan timeframe 1m, 5m, atau 15m.")
        return
        
    st.markdown("### :material/hourglass_top: Detail Analisis Waktu Transaksi")
    
    st.markdown(f"""
    **Dataset Info:**
    - Ticker: {cand['Ticker']}
    - Timeframe: {timing['interval']}
    - Trading Days: {timing['trading_days']}
    - Period: {timing.get('date_start')} to {timing.get('date_end')}
    """)
    
    windows = timing.get("windows", [])
    if not windows:
        st.warning("Tidak cukup data observasi intraday.")
        return
        
    df_windows = pd.DataFrame(windows)
    
    tab1, tab2, tab3 = st.tabs(["Performa Berdasarkan Waktu", "Matriks Waktu Beli vs Jual", "Analisis Awal Sesi"])
    
    with tab1:
        st.markdown("#### Rata-rata Keuntungan & Akurasi Berdasarkan Waktu")
        
        # Dual-axis chart
        fig = go.Figure()
        
        # Add Bar trace for Median Return
        fig.add_trace(go.Bar(
            x=df_windows["time"],
            y=df_windows["median_return"],
            name="Rata-rata Untung (%)",
            marker_color=df_windows["median_return"].apply(lambda x: "green" if x > 0 else "red")
        ))
        
        # Add Line trace for Win Rate on secondary Y-axis
        fig.add_trace(go.Scatter(
            x=df_windows["time"],
            y=df_windows["win_rate"],
            name="Akurasi Menang (%)",
            yaxis="y2",
            mode="lines+markers",
            line=dict(color="orange", width=2)
        ))
        
        # Create axis objects
        fig.update_layout(
            title="Profil Pergerakan Harian",
            xaxis_title="Waktu",
            yaxis=dict(title="Rata-rata Untung (%)", side="left"),
            yaxis2=dict(title="Akurasi Menang (%)", side="right", overlaying="y", range=[0, 100]),
            height=400,
            margin=dict(l=0, r=0, t=40, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("#### Profil Lonjakan Volume (RVOL)")
        fig_vol = px.bar(
            df_windows, x="time", y="rvol", 
            title="Lonjakan Volume Relatif Berdasarkan Waktu",
            color="rvol", color_continuous_scale="Blues"
        )
        fig_vol.add_hline(y=1.0, line_dash="dash", line_color="red")
        st.plotly_chart(fig_vol, use_container_width=True)
        
        st.markdown("#### Distribusi Detail")
        st.dataframe(
            df_windows[["time", "observations", "win_rate", "avg_return", "median_return", "rvol", "avg_drawdown"]].style.format({
                "win_rate": "{:.1f}%",
                "avg_return": "{:.3f}%",
                "median_return": "{:.3f}%",
                "rvol": "{:.2f}x",
                "avg_drawdown": "{:.3f}%"
            }),
            use_container_width=True
        )

    with tab2:
        st.markdown("#### Matriks Keuntungan Beli vs Jual")
        st.caption("Baris = Waktu Beli, Kolom = Waktu Jual. Angka menunjukkan Rata-rata Keuntungan (%).")
        
        with st.spinner("Generating Matrix..."):
            matrix_data = generate_entry_exit_matrix(df_raw, timing["interval"])
            
        if matrix_data["available"]:
            times = matrix_data["times"]
            matrix = matrix_data["matrix"]
            
            # Format matrix for heatmap
            heatmap_data = []
            for entry_time in times:
                row = []
                for exit_time in times:
                    val = matrix.get(entry_time, {}).get(exit_time)
                    if val:
                        row.append(val["median_return"])
                    else:
                        row.append(None)
                heatmap_data.append(row)
                
            fig_hm = go.Figure(data=go.Heatmap(
                z=heatmap_data,
                x=times,
                y=times,
                colorscale="RdYlGn",
                zmid=0,
                hoverongaps=False
            ))
            fig_hm.update_layout(
                xaxis_title="Waktu Exit",
                yaxis_title="Waktu Entry",
                yaxis_autorange="reversed",
                height=600
            )
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info("Data tidak mencukupi untuk membuat matrix.")

    with tab3:
        st.markdown("#### Analisis Pergerakan Awal Sesi")
        with st.spinner("Menganalisis Pergerakan Awal Sesi..."):
            orb_data = analyze_opening_range(df_raw, timing["interval"])
            
        if orb_data["available"]:
            stats = orb_data["stats"]["First_15m"]
            total = stats["total"]
            
            if total > 0:
                st.write(f"Berdasarkan **{total} hari perdagangan** terakhir:")
                c1, c2 = st.columns(2)
                
                up_rate = (stats["breakout_up"] / total) * 100
                down_rate = (stats["breakout_down"] / total) * 100
                
                with c1:
                    st.metric(
                        "Peluang Tembus Atas (Breakout Up)", 
                        f"{up_rate:.1f}%",
                        f"+{stats['avg_cont_up']:.2f}% rata-rata naik lanjutan"
                    )
                
                with c2:
                    st.metric(
                        "Peluang Tembus Bawah (Breakout Down)", 
                        f"{down_rate:.1f}%",
                        f"-{stats['avg_cont_down']:.2f}% rata-rata turun lanjutan",
                        delta_color="inverse"
                    )
            else:
                st.info("Tidak cukup rentang hari untuk menghitung statistik awal sesi.")
        else:
            st.info("Data tidak mencukupi untuk analisis ORB.")
