import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

from src.data_loader import fetch_stock_data
from src.company_metadata import get_company_metadata
from src.indicators import calculate_indicators, get_technical_score
from src.news_loader import get_contextual_news
from src.sentiment import analyze_news_dataframe, aggregate_daily_sentiment, merge_sentiment_with_stock
from src.prediction import train_and_predict
from src.trading_strategy import generate_signal, get_signal_explanation, calculate_entry_target_stoploss, generate_technical_signals_series
from src.llm_explanation import generate_explanation
from src.backtesting import run_backtest
from src.historical_timing import analyze_intraday_timing
from src.ui.timing_ui import render_full_timing_analysis
from src.realtime_provider import market_provider
from src.prediction_history import get_accuracy_metrics
from src.ui.chart_component import render_tradingview_chart
from src.visualization import (
    create_candlestick_chart,
    create_prediction_chart,
    create_sentiment_trend_chart,
    COLORS
)

def render_stock_analysis(ticker: str):
    st.title(f":material/analytics: Analisis Saham: {ticker}")
    
    meta = get_company_metadata(ticker)
    
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.markdown(f"**{meta['company']}**")
        st.markdown(f"Sector: `{meta['sector']}` | Industry: `{meta['industry']}`")
    with col_t2:
        interval_options = {"1d": "Harian", "1h": "1 Jam", "15m": "15 Menit", "5m": "5 Menit", "1m": "1 Menit"}
        selected_interval = st.selectbox("Periode Waktu", list(interval_options.keys()), format_func=lambda x: interval_options[x], index=0)
    
    # ─── Fetch Data ─────────────────────────────────────────
    end_date = datetime.now()
    if selected_interval == "1m":
        start_date = end_date - timedelta(days=6)
    elif selected_interval in ["5m", "15m"]:
        start_date = end_date - timedelta(days=59)
    elif selected_interval == "1h":
        start_date = end_date - timedelta(days=729)
    else:
        start_date = end_date - timedelta(days=730)
    
    with st.spinner("Mengambil data teknikal & sentimen..."):
        # 1. Fetch Stock Price
        df_stock = fetch_stock_data(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), interval=selected_interval)
        
        # 2. Fetch News (Contextual)
        df_news = get_contextual_news(ticker)
        
        if df_stock.empty:
            st.error("Gagal mengambil data saham.")
            return
            
        # 3. Calculate Indicators
        df_tech = calculate_indicators(df_stock)
        
        # 4. Analyze Sentiment & Relevance
        df_news_analyzed = analyze_news_dataframe(df_news, ticker)
        daily_sentiment = aggregate_daily_sentiment(df_news_analyzed, ticker)
        
        # 5. Merge Data
        df_merged = merge_sentiment_with_stock(df_tech, daily_sentiment)
        
        # 6. ML Prediction (use interval in ticker name for separate caching)
        pred_results = train_and_predict(df_merged, ticker=f"{ticker}_{selected_interval}")
        
    latest = df_tech.iloc[-1]
    prev = df_tech.iloc[-2]
    current_price = latest['Close']
    price_change = current_price - prev['Close']
    pct_change = (price_change / prev['Close']) * 100
    
    # ─── Market Status & Connection ──────────────────────────
    mkt_status = market_provider.get_market_status(ticker)
    st.markdown(f"""
    <div style="display: flex; gap: 15px; margin-bottom: 20px; align-items: center;">
        <div style="background: #161b22; padding: 10px 15px; border-radius: 6px; border: 1px solid #30363d;">
            <span style="color: #8b949e; font-size: 0.8rem; text-transform: uppercase;">Market</span><br>
            <strong style="color: {'#2ea043' if mkt_status['market_status'] == 'OPEN' else '#8b949e'};">{ '🟢' if mkt_status['market_status'] == 'OPEN' else '⚪'} {mkt_status['market_status']}</strong>
        </div>
        <div style="background: #161b22; padding: 10px 15px; border-radius: 6px; border: 1px solid #30363d;">
            <span style="color: #8b949e; font-size: 0.8rem; text-transform: uppercase;">Data</span><br>
            <strong style="color: {'#f59e0b' if 'DELAYED' in mkt_status['data_status'] else '#4ecdc4'};">{mkt_status['data_status']}</strong>
        </div>
        <div style="background: #161b22; padding: 10px 15px; border-radius: 6px; border: 1px solid #30363d;">
            <span style="color: #8b949e; font-size: 0.8rem; text-transform: uppercase;">Update</span><br>
            <strong>{mkt_status['last_update']}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Harga Terakhir", f"Rp {current_price:,.0f}", f"{price_change:+,.0f} ({pct_change:+.2f}%)")
    with col2:
        tech_score = get_technical_score(latest)
        st.metric("Skor Teknikal", f"{tech_score}/5", "Kuat" if tech_score >= 4 else "Lemah" if tech_score <= 2 else "Netral")
    with col3:
        if pred_results and pred_results.get("status") == "success":
            pred_1d = pred_results.get("horizons", {}).get("1d", {})
            pred = pred_1d.get("prediction", "N/A")
            prob = pred_1d.get("probability", 0) * 100
            price_target = pred_1d.get("predicted_price")
            target_str = f"Rp {price_target:,.0f}" if price_target else f"{prob:.1f}% Akurasi"
            st.metric("Prediksi AI", f"{pred}", target_str,
                      delta_color="normal" if pred == "UP" else "inverse")
    with col4:
        if not daily_sentiment.empty:
            avg_sent = daily_sentiment.iloc[-1]["average_sentiment"]
            st.metric("Sentimen Berita", f"{avg_sent:+.2f}", "Terbaru")
        else:
            st.metric("Sentimen Berita", "Tidak Ada Data", "")
            
    # ─── "So, What?" (LLM Explanation) ──────────────────────
    st.markdown("---")
    st.subheader(":material/psychology: Kesimpulan Sederhana")
    
    with st.spinner("Membuat kesimpulan dengan AI..."):
        explanation_data = {
            "ticker": ticker,
            "company": meta['company'],
            "price": current_price,
            "change_pct": pct_change,
            "rsi": latest.get('RSI', 50),
            "macd": "positive" if latest.get('MACD', 0) > latest.get('MACD_Signal', 0) else "negative",
            "technical_score": tech_score,
            "news_impact": df_news_analyzed.iloc[0]['impact'] if not df_news_analyzed.empty else "UNKNOWN",
            "prediction_1d": pred_results.get("horizons", {}).get("1d", {}).get("prediction", "UNKNOWN") if pred_results else "UNKNOWN",
            "prediction_5d": pred_results.get("horizons", {}).get("5d", {}).get("prediction", "UNKNOWN") if pred_results else "UNKNOWN",
            "prediction_20d": pred_results.get("horizons", {}).get("20d", {}).get("prediction", "UNKNOWN") if pred_results else "UNKNOWN",
            "predicted_price_1d": pred_results.get("horizons", {}).get("1d", {}).get("predicted_price") if pred_results else None,
            "prediction_probability": pred_results.get("horizons", {}).get("1d", {}).get("probability", 0) if pred_results else 0
        }
        explanation = generate_explanation(explanation_data)
        st.info(explanation)
        
    st.markdown("---")
    
    # ─── Tabs ──────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Grafik Teknikal", "Berita & Sentimen", "Prediksi AI", "Rencana Transaksi", "Uji Balik (Backtest)", "Waktu Transaksi"])
    
    with tab1:
        st.markdown("### 📈 Grafik Interaktif")
        
        # Calculate technical levels for chart overlay
        support = latest.get("Support", current_price * 0.95)
        resistance = latest.get("Resistance", current_price * 1.05)
        tp = latest.get("Take_Profit", current_price * 1.03)
        sl = latest.get("Stop_Loss", current_price * 0.97)
        
        render_tradingview_chart(
            df=df_tech,
            ticker=ticker,
            entry_zone=(support, current_price * 1.01),
            tp=tp,
            sl=sl,
            height=500
        )
        
    with tab2:
        if not df_news_analyzed.empty:
            st.plotly_chart(create_sentiment_trend_chart(daily_sentiment, ticker), use_container_width=True)
            st.markdown("### :material/newspaper: Berita Relevan Terbaru")
            
            for _, row in df_news_analyzed.head(10).iterrows():
                with st.expander(f"{row['title']} ({row['date']}) - Relevance: {row['relevance']}"):
                    st.write(f"**Source:** {row['source']}")
                    st.write(f"**Impact:** {row['impact']}")
                    st.write(f"**Reason:** {row['impact_reason']}")
                    if pd.notna(row['description']) and row['description']:
                        st.write(f"**Snippet:** {row['description']}")
                    st.write(f"[Read Article]({row['url']})")
        else:
            st.info("Tidak ada berita relevan dalam 7 hari terakhir.")
            
    with tab3:
        if pred_results and pred_results["status"] == "success":
            horizons = pred_results.get("horizons", {})
            st.markdown("### 🔮 AI Future Forecast")
            
            h_keys = list(horizons.keys())
            if len(h_keys) > 0:
                h1 = horizons.get(h_keys[0], {})
                h2 = horizons.get(h_keys[len(h_keys)//2], {}) if len(h_keys) > 2 else {}
                h3 = horizons.get(h_keys[-1], {}) if len(h_keys) > 1 else {}
                
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    target_str = f"Target: Rp {h1.get('predicted_price'):,.0f}" if h1.get("predicted_price") else f"{h1.get('probability', 0)*100:.1f}% Akurasi"
                    st.metric(f"Terdekat (+{h_keys[0]})", h1.get("prediction", "N/A"), 
                              target_str, delta_color="normal" if h1.get("prediction") == "UP" else "inverse")
                with col_m2:
                    target_str = f"Target: Rp {h2.get('predicted_price'):,.0f}" if h2.get("predicted_price") else f"{h2.get('probability', 0)*100:.1f}% Akurasi"
                    st.metric(f"Menengah (+{h_keys[len(h_keys)//2]})", h2.get("prediction", "N/A") if h2 else "N/A", 
                              target_str, delta_color="normal" if h2.get("prediction") == "UP" else "inverse")
                with col_m3:
                    target_str = f"Target: Rp {h3.get('predicted_price'):,.0f}" if h3.get("predicted_price") else f"{h3.get('probability', 0)*100:.1f}% Akurasi"
                    st.metric(f"Terjauh (+{h_keys[-1]})", h3.get("prediction", "N/A") if h3 else "N/A", 
                              target_str, delta_color="normal" if h3.get("prediction") == "UP" else "inverse")
                st.caption(f"Akurasi Validasi Model Terjauh: {h3.get('accuracy', 0):.2%}")
                
            st.markdown("---")
            
            # AI Track Record
            acc_metrics = get_accuracy_metrics(ticker.split('_')[0])
            st.markdown("### 🏆 Rekam Jejak AI (AI Track Record)")
            
            col_tk1, col_tk2, col_tk3, col_tk4 = st.columns(4)
            col_tk1.metric("Akurasi Arah", f"{acc_metrics['directional_accuracy']:.1%}")
            col_tk2.metric("MAE (T1)", f"Rp {acc_metrics['mae_t1']:.0f}")
            col_tk3.metric("RMSE (T1)", f"Rp {acc_metrics['rmse_t1']:.0f}")
            col_tk4.metric("Total Prediksi", f"{acc_metrics['total_completed']}")
            
            st.info("⚠️ **Peringatan Model:** Prediksi AI adalah perkiraan berdasarkan pola historis, bukan jaminan. Akurasi masa lalu tidak menjamin akurasi masa depan.")
            
            st.markdown("---")
            st.markdown(f"#### Grafik AI Future Forecast ({interval_options[selected_interval]})")
            
            # Extract future prediction for Chart (from the base horizon which holds the assembled trajectory)
            base_horizon = horizons.get(h_keys[0], {})
            pred_path = base_horizon.get("predicted_path", [])
            lb = base_horizon.get("lower_bound", [])
            ub = base_horizon.get("upper_bound", [])
            
            render_tradingview_chart(
                df=df_merged,
                ticker=ticker,
                prediction_path=pred_path,
                lower_bound=lb,
                upper_bound=ub,
                current_price=current_price,
                height=500
            )
            
            st.markdown("---")
            with st.expander("📊 Eksperimen Test Period (Training Configuration)"):
                st.markdown("Bandingkan pengaruh rasio pembagian data (Train/Test Split) terhadap performa model forecast.")
                st.info("Nilai 80% artinya 80% data paling awal digunakan untuk Training, dan 20% data paling baru untuk Test/Validasi.")
                
                exp_col1, exp_col2 = st.columns([1, 1])
                with exp_col1:
                    exp_split = st.select_slider(
                        "Test Period Split Ratio",
                        options=[0.5, 0.6, 0.7, 0.8, 0.9],
                        value=0.8,
                        format_func=lambda x: f"Train {int(x*100)}% / Test {int((1-x)*100)}%"
                    )
                with exp_col2:
                    st.write("") # spacing
                    st.write("")
                    run_exp = st.button("Jalankan Eksperimen & Lihat Hasil")
                    
                if run_exp:
                    with st.spinner("Melatih ulang model untuk bereksperimen..."):
                        exp_results = train_and_predict(df_merged, ticker=f"{ticker}_{selected_interval}", train_ratio=exp_split)
                        if exp_results["status"] == "success":
                            st.success("Eksperimen selesai!")
                            exp_horizons = exp_results.get("horizons", {})
                            
                            rows = []
                            for h_k, h_v in exp_horizons.items():
                                rows.append({
                                    "Horizon": f"+{h_k}",
                                    "Akurasi Arah": f"{h_v.get('accuracy', 0):.1%}",
                                    "RMSE (Error)": f"Rp {h_v.get('rmse', 0):.0f}",
                                    "Prediksi Terakhir": h_v.get('prediction', 'N/A')
                                })
                            
                            st.dataframe(pd.DataFrame(rows), use_container_width=True)
                        else:
                            st.error("Gagal menjalankan eksperimen.")
            
    with tab4:
        st.subheader(":material/ads_click: Rencana Transaksi")
        if pred_results and pred_results["status"] == "success":
            pred = pred_results["today_prediction"]
            prob = pred_results["probability"]
            signal = generate_signal(tech_score, pred, prob)
            explanation = get_signal_explanation(signal, tech_score, pred, prob, 0.6)
            
            if signal == "BUY":
                st.success(explanation)
            elif signal == "SELL":
                st.error(explanation)
            else:
                st.info(explanation)
                
            support = latest.get("Support", current_price * 0.95)
            resistance = latest.get("Resistance", current_price * 1.05)
            
            plan = calculate_entry_target_stoploss(current_price, pred, support, resistance)
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Area Beli", f"Rp {plan['entry_price']:,.0f}")
            with col_b:
                st.metric("Target Jual", f"Rp {plan['target_price']:,.0f}")
            with col_c:
                st.metric("Batas Rugi (Stop Loss)", f"Rp {plan['stop_loss']:,.0f}")
        else:
            st.warning("Prediksi belum tersedia untuk membuat Trading Plan.")

    with tab5:
        st.subheader(":material/science: Uji Balik (Backtest)")
        st.markdown("Simulasi hasil transaksi jika strategi ini dijalankan pada waktu lampau.")
        
        # Form backtesting
        with st.form("backtest_form"):
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                init_cap = st.number_input("Modal Awal (Rp)", min_value=1_000_000, max_value=1_000_000_000, value=10_000_000, step=1_000_000)
            with col_b2:
                target_pct = st.number_input("Target Profit (%)", min_value=1.0, max_value=50.0, value=5.0, step=0.5)
            with col_b3:
                sl_pct = st.number_input("Stop Loss (%)", min_value=1.0, max_value=50.0, value=3.0, step=0.5)
            
            run_bt = st.form_submit_button("Jalankan Simulasi")
            
        if run_bt:
            with st.spinner("Menjalankan simulasi historis..."):
                df_signals = generate_technical_signals_series(df_tech)
                bt_results = run_backtest(df_signals, initial_capital=init_cap, target_pct=target_pct, stop_loss_pct=sl_pct)
                
                metrics = bt_results["metrics"]
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total Return", f"{metrics['total_return']}%")
                c2.metric("Win Rate", f"{metrics['win_rate']}%")
                c3.metric("Total Trades", metrics['num_trades'])
                c4.metric("Max Drawdown", f"{metrics['max_drawdown']}%")
                
                c_eq = st.container()
                
                st.markdown("#### Detail Trade")
                st.dataframe(bt_results["trades"], use_container_width=True)
                
                if not bt_results["equity_curve"].empty:
                    fig_eq = go.Figure()
                    fig_eq.add_trace(go.Scatter(
                        x=bt_results["equity_curve"].index,
                        y=bt_results["equity_curve"]["equity"],
                        mode='lines',
                        name='Strategy Equity',
                        line=dict(color=COLORS['blue'])
                    ))
                    fig_eq.update_layout(
                        title="Equity Curve",
                        xaxis_title="Date",
                        yaxis_title="Balance (Rp)",
                        template="plotly_dark",
                        height=300,
                        margin=dict(l=0, r=0, t=30, b=0)
                    )
                    c_eq.plotly_chart(fig_eq, use_container_width=True)

    with tab6:
        with st.spinner("Analyzing historical timing..."):
            timing_data = analyze_intraday_timing(ticker, df_stock, selected_interval)
            cand = {
                "Ticker": ticker,
                "Historical_Timing": timing_data,
                "df": df_stock
            }
            render_full_timing_analysis(cand, df_stock)
