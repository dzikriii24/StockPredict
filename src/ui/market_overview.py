import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go

from src.data_loader import TICKER_INFO, fetch_stock_data
from src.company_metadata import metadata_manager
from src.visualization import COLORS, create_candlestick_chart, create_prediction_chart
from src.indicators import calculate_indicators, get_technical_score
from src.prediction import train_and_predict
from src.llm_explanation import generate_explanation
from src.short_term_scanner import fast_scan_universe, run_deep_analysis, get_scanner_explanation

@st.cache_data(ttl=60)
def fetch_market_snapshot() -> pd.DataFrame:
    """Fetch 5-day history for all tracked tickers to calculate 1-day change."""
    tickers = list(TICKER_INFO.keys())
    
    data = yf.download(tickers, period="5d", group_by="ticker", progress=False)
    
    snapshot = []
    for ticker in tickers:
        try:
            if isinstance(data.columns, pd.MultiIndex):
                df = data[ticker].dropna()
            else:
                df = data.dropna()
                
            if len(df) >= 2:
                current_price = float(df['Close'].iloc[-1])
                prev_price = float(df['Close'].iloc[-2])
                volume = float(df['Volume'].iloc[-1])
                pct_change = ((current_price - prev_price) / prev_price) * 100
                
                meta = metadata_manager.get_metadata(ticker)
                snapshot.append({
                    "Ticker": ticker,
                    "Company": meta["company"],
                    "Sector": meta["sector"],
                    "Industry": meta["industry"],
                    "Price": current_price,
                    "Change (%)": round(pct_change, 2),
                    "Volume": volume
                })
        except Exception:
            pass
            
    return pd.DataFrame(snapshot)

def render_mini_analysis(ticker: str, company: str, current_price: float, pct_change: float, interval: str = "1d", category: str = "default"):
    """Render mini chart and text prediction for a stock inside an expander."""
    end_date = datetime.now()
    # Set start date dynamically based on interval
    if interval == "1m":
        start_date = end_date - timedelta(days=6)
    elif interval in ["5m", "15m"]:
        start_date = end_date - timedelta(days=59)
    elif interval == "1h":
        start_date = end_date - timedelta(days=729)
    else:
        start_date = end_date - timedelta(days=730)
        
    with st.spinner(f"Menganalisis {ticker}..."):
        df = fetch_stock_data(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), interval=interval)
        if df.empty:
            st.error("Data tidak tersedia.")
            return
            
        df_tech = calculate_indicators(df)
        pred_results = train_and_predict(df_tech, ticker=f"{ticker}_{interval}")
        
        # Text explanation
        latest = df_tech.iloc[-1]
        tech_score = get_technical_score(latest)
        explanation_data = {
            "ticker": ticker,
            "company": company,
            "price": current_price,
            "change_pct": pct_change,
            "rsi": latest.get('RSI', 50),
            "macd": "positive" if latest.get('MACD', 0) > latest.get('MACD_Signal', 0) else "negative",
            "technical_score": tech_score,
            "news_impact": "UNKNOWN", # We skip news sentiment for speed in mini analysis
            "prediction_1d": pred_results.get("horizons", {}).get("1d", {}).get("prediction", "UNKNOWN") if pred_results else "UNKNOWN",
            "prediction_5d": pred_results.get("horizons", {}).get("5d", {}).get("prediction", "UNKNOWN") if pred_results else "UNKNOWN",
            "prediction_20d": pred_results.get("horizons", {}).get("20d", {}).get("prediction", "UNKNOWN") if pred_results else "UNKNOWN",
            "prediction_probability": pred_results.get("probability", 0) if pred_results else 0
        }
        
        st.markdown("##### Prediksi Pergerakan Harga (AI)")
        st.markdown("Perkiraan arah harga menggunakan kecerdasan buatan.")
        
        if pred_results and pred_results.get("status") == "success":
            horizons = pred_results.get("horizons", {})
            h_keys = list(horizons.keys())
            
            if len(h_keys) > 0:
                col1, col2, col3 = st.columns(3)
                
                h1 = horizons.get(h_keys[0], {})
                target_str = f"Target: Rp {h1.get('predicted_price'):,.0f}" if h1.get("predicted_price") else f"{h1.get('probability', 0)*100:.1f}% Prob"
                col1.metric(f"Terdekat (+{h_keys[0]})", h1.get("prediction", "N/A"), target_str,
                          delta_color="normal" if h1.get("prediction") == "UP" else "inverse")
                
                h2 = horizons.get(h_keys[len(h_keys)//2], {}) if len(h_keys) > 2 else {}
                if h2:
                    target_str = f"Target: Rp {h2.get('predicted_price'):,.0f}" if h2.get("predicted_price") else f"{h2.get('probability', 0)*100:.1f}% Prob"
                    col2.metric(f"Menengah (+{h_keys[len(h_keys)//2]})", h2.get("prediction", "N/A"), target_str,
                              delta_color="normal" if h2.get("prediction") == "UP" else "inverse")
                          
                h3 = horizons.get(h_keys[-1], {}) if len(h_keys) > 1 else {}
                if h3:
                    target_str = f"Target: Rp {h3.get('predicted_price'):,.0f}" if h3.get("predicted_price") else f"{h3.get('probability', 0)*100:.1f}% Prob"
                    col3.metric(f"Terjauh (+{h_keys[-1]})", h3.get("prediction", "N/A"), target_str,
                              delta_color="normal" if h3.get("prediction") == "UP" else "inverse")
        
        horizons = pred_results.get("horizons", {}) if pred_results and pred_results.get("status") == "success" else {}
        h_keys = list(horizons.keys())
        base_horizon = horizons.get(h_keys[0], {}) if h_keys else {}
        
        pred_path = base_horizon.get("predicted_path", [])
        lb = base_horizon.get("lower_bound", [])
        ub = base_horizon.get("upper_bound", [])
        
        from src.ui.chart_component import render_tradingview_chart
        render_tradingview_chart(
            df=df_tech,
            ticker=ticker,
            prediction_path=pred_path,
            lower_bound=lb,
            upper_bound=ub,
            current_price=current_price,
            height=400
        )
        
        explanation = generate_explanation(explanation_data)
        st.info(explanation)


def render_market_overview():
    st.title(":material/dashboard: Ringkasan Pasar")
    st.markdown("Ringkasan kondisi pasar saham berdasarkan daftar pantauan sistem dan pergerakan Indeks Harga Saham Gabungan (IHSG).")
    
    col_title, col_time = st.columns([3, 1])
    with col_time:
        interval_options = {"1d": "Harian", "1h": "1 Jam", "15m": "15 Menit", "5m": "5 Menit", "1m": "1 Menit"}
        selected_interval = st.selectbox("Periode Waktu", list(interval_options.keys()), format_func=lambda x: interval_options[x], index=0, key="mo_timeframe")
    
    # ─── IHSG CHART & PREDICTION ──────────────────────────────────────
    st.markdown(f"### IHSG (Indeks Harga Saham Gabungan) Tren & Prediksi ({interval_options[selected_interval]})")
    
    end_date = datetime.now()
    if selected_interval == "1m":
        start_date = end_date - timedelta(days=6)
    elif selected_interval in ["5m", "15m"]:
        start_date = end_date - timedelta(days=59)
    elif selected_interval == "1h":
        start_date = end_date - timedelta(days=729)
    else:
        start_date = end_date - timedelta(days=730)
    
    with st.spinner("Memuat data dan prediksi IHSG..."):
        try:
            df_ihsg = fetch_stock_data("^JKSE", start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), interval=selected_interval)
        except ValueError:
            df_ihsg = pd.DataFrame()
            st.warning(f"Yahoo Finance sedang tidak menyediakan data intraday ({selected_interval}) untuk IHSG (^JKSE). Coba gunakan periode Harian (1d).")
        except Exception as e:
            df_ihsg = pd.DataFrame()
            st.error(f"Gagal memuat data IHSG: {e}")
        if not df_ihsg.empty:
            df_ihsg_tech = calculate_indicators(df_ihsg)
            ihsg_pred = train_and_predict(df_ihsg_tech, f"^JKSE_{selected_interval}")
            
            if ihsg_pred and ihsg_pred["status"] == "success":
                horizons = ihsg_pred.get("horizons", {})
            else:
                horizons = {}
                
            col_chart, col_pred = st.columns([2, 1])
            
            with col_chart:
                h_keys = list(horizons.keys())
                base_horizon = horizons.get(h_keys[0], {}) if h_keys else {}
                
                pred_path = base_horizon.get("predicted_path", [])
                lb = base_horizon.get("lower_bound", [])
                ub = base_horizon.get("upper_bound", [])
                
                from src.ui.chart_component import render_tradingview_chart
                render_tradingview_chart(
                    df=df_ihsg_tech,
                    ticker="^JKSE (IHSG)",
                    prediction_path=pred_path,
                    lower_bound=lb,
                    upper_bound=ub,
                    current_price=df_ihsg_tech.iloc[-1]["Close"] if not df_ihsg_tech.empty else None,
                    height=450
                )
                
            with col_pred:
                st.markdown("#### Prediksi Pasar (AI)")
                st.markdown("Prediksi pergerakan IHSG menggunakan model Machine Learning Multi-Horizon.")
                
                if ihsg_pred and ihsg_pred["status"] == "success":
                    
                    h_keys = list(horizons.keys())
                    if len(h_keys) > 0:
                        h1 = horizons.get(h_keys[0], {})
                        target_str = f"Target: Rp {h1.get('predicted_price'):,.0f}" if h1.get("predicted_price") else f"{h1.get('probability', 0)*100:.1f}% Prob"
                        st.metric(f"Terdekat (+{h_keys[0]})", h1.get("prediction", "N/A"), target_str,
                                  delta_color="normal" if h1.get("prediction") == "UP" else "inverse")
                        
                        h2 = horizons.get(h_keys[len(h_keys)//2], {}) if len(h_keys) > 2 else {}
                        if h2:
                            target_str = f"Target: Rp {h2.get('predicted_price'):,.0f}" if h2.get("predicted_price") else f"{h2.get('probability', 0)*100:.1f}% Prob"
                            st.metric(f"Menengah (+{h_keys[len(h_keys)//2]})", h2.get("prediction", "N/A"), target_str,
                                      delta_color="normal" if h2.get("prediction") == "UP" else "inverse")
                                  
                        h3 = horizons.get(h_keys[-1], {}) if len(h_keys) > 1 else {}
                        if h3:
                            target_str = f"Target: Rp {h3.get('predicted_price'):,.0f}" if h3.get("predicted_price") else f"{h3.get('probability', 0)*100:.1f}% Prob"
                            st.metric(f"Terjauh (+{h_keys[-1]})", h3.get("prediction", "N/A"), target_str,
                                      delta_color="normal" if h3.get("prediction") == "UP" else "inverse")
                else:
                    st.error(f"Gagal melatih model untuk IHSG. {ihsg_pred.get('message', '')}")
        else:
            st.warning("Gagal mengunduh data IHSG dari server.")
            
    # ─── IHSG MARKET TIMING ─────────────────────────────────────────────
    st.markdown("### Analisis Waktu Transaksi (IHSG)")
    if selected_interval in ["1m", "5m", "15m", "30m", "1h"]:
        with st.spinner("Analyzing Market-Wide Timing..."):
            from src.historical_timing import analyze_intraday_timing
            from src.ui.timing_ui import render_full_timing_analysis
            
            # Re-fetch with a wider date range if necessary for timing, or use df_ihsg
            # Ensure df_ihsg exists and is not empty
            if 'df_ihsg' in locals() and not df_ihsg.empty:
                timing_ihsg = analyze_intraday_timing("^JKSE", df_ihsg, selected_interval)
                cand_ihsg = {
                    "Ticker": "^JKSE (IHSG)",
                    "Historical_Timing": timing_ihsg,
                    "df": df_ihsg
                }
                with st.expander("Detail Analisis Waktu Transaksi Pasar"):
                    render_full_timing_analysis(cand_ihsg, df_ihsg)
            else:
                st.info("Data IHSG tidak tersedia untuk analisis waktu.")
    else:
        st.info("Pilih timeframe intraday (1m, 5m, 15m, 30m, 1h) untuk melihat Historical Market Timing.")
            
    st.markdown("---")
    
    # ─── BREADTH & MOVERS ─────────────────────────────────────────────
    with st.spinner("Mengambil data pasar terkini..."):
        df = fetch_market_snapshot()
        
    if df.empty:
        st.warning("Gagal mengambil data pasar. Coba lagi nanti.")
        return
        
    # Metrics
    total_stocks = len(df)
    advancing = len(df[df["Change (%)"] > 0])
    declining = len(df[df["Change (%)"] < 0])
    
    avg_return = df["Change (%)"].mean()
    
    # Render KPI Cards
    st.markdown("### Kondisi Pasar Saat Ini")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Total Dipantau</div><div class='kpi-value'>{total_stocks}</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Harga Naik</div><div class='kpi-value kpi-green'>{advancing}</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Harga Turun</div><div class='kpi-value kpi-red'>{declining}</div></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>Rata-rata Perubahan</div><div class='kpi-value {'kpi-green' if avg_return > 0 else 'kpi-red'}'>{avg_return:+.2f}%</div></div>", unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Top Movers
    col_gain, col_lose, col_vol = st.columns(3)
    
    with col_gain:
        st.markdown("#### Saham Naik Tertinggi")
        gainers = df.nlargest(5, "Change (%)")[["Ticker", "Company", "Change (%)", "Price"]]
        for _, row in gainers.iterrows():
            ticker = row['Ticker']
            clean_ticker = ticker.replace('.JK', '')
            pct = row['Change (%)']
            with st.expander(f"{clean_ticker} — +{pct}%", expanded=True):
                render_mini_analysis(ticker, row['Company'], row['Price'], pct, interval=selected_interval, category="gainers")
            
    with col_lose:
        st.markdown("#### Saham Turun Terdalam")
        losers = df.nsmallest(5, "Change (%)")[["Ticker", "Company", "Change (%)", "Price"]]
        for _, row in losers.iterrows():
            ticker = row['Ticker']
            clean_ticker = ticker.replace('.JK', '')
            pct = row['Change (%)']
            with st.expander(f"{clean_ticker} — {pct}%", expanded=True):
                render_mini_analysis(ticker, row['Company'], row['Price'], pct, interval=selected_interval, category="losers")
            
    with col_vol:
        st.markdown("#### Paling Banyak Ditransaksikan")
        active = df.nlargest(5, "Volume")[["Ticker", "Company", "Volume", "Change (%)", "Price"]]
        for _, row in active.iterrows():
            ticker = row['Ticker']
            clean_ticker = ticker.replace('.JK', '')
            vol_m = row['Volume'] / 1_000_000
            pct = row['Change (%)']
            prefix = "+" if pct > 0 else ""
            with st.expander(f"{clean_ticker} ({vol_m:.1f}M) — {prefix}{pct}%", expanded=True):
                render_mini_analysis(ticker, row['Company'], row['Price'], pct, interval=selected_interval, category="active")
                
    st.markdown("---")
    st.markdown("### Kandidat Pantauan Jangka Pendek (Top 3)")
    st.markdown("Peluang pergerakan jangka pendek berdasarkan tren dan algoritma kecerdasan buatan.")
    
    with st.spinner("Memindai kandidat short-term terbaik..."):
        fast_cands = fast_scan_universe("1d")
        if fast_cands:
            top_3 = run_deep_analysis(fast_cands, top_n=3, interval="1d")
            
            c1, c2, c3 = st.columns(3)
            cols = [c1, c2, c3]
            
            for i, cand in enumerate(top_3):
                with cols[i]:
                    clean = cand['Ticker'].replace('.JK', '')
                    sig = cand.get("Signal", {}).get("signal", "N/A")
                    rr = cand.get("Risk_Reward", {})
                    entry = cand.get("Entry", {})
                    
                    st.markdown(f"**{clean}** · Rp {cand['Price']:,.0f}")
                    st.write(f"Score: **{cand['Score']:.0f}**/100 · {sig}")
                    st.write(f"Area Beli: Rp {entry.get('preferred_low', 0):,.0f}-{entry.get('preferred_high', 0):,.0f}")
                    st.write(f"R/R: {rr.get('display', 'N/A')} · Prediksi AI: {cand.get('ML', {}).get('prediction', 'N/A')}")
                    st.caption(get_scanner_explanation(cand)[:100] + "...")
        else:
            st.warning("Belum ada data kandidat.")
            
    st.info("Buka halaman **Pemindai Jangka Pendek** dari menu navigasi kiri untuk analisis lengkap.")

