import streamlit as st
from src.company_metadata import get_company_metadata
from src.data_loader import fetch_stock_data
from src.indicators import calculate_indicators, get_technical_score
from src.prediction import train_and_predict
from src.news_loader import get_contextual_news
from src.sentiment import analyze_news_dataframe, aggregate_daily_sentiment, merge_sentiment_with_stock
from src.trading_strategy import generate_signal, get_signal_explanation
from src.short_term_scanner import run_deep_analysis, get_scanner_explanation
from datetime import datetime, timedelta

def render_presentation_mode(ticker: str):
    st.title(":material/smart_display: Rangkuman Presentasi")
    
    meta = get_company_metadata(ticker)
    
    st.markdown(f"### {meta['company']} ({ticker})")
    st.markdown(f"**Sector:** {meta['sector']} | **Industry:** {meta['industry']}")
    
    with st.spinner("Membuat rangkuman presentasi..."):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        try:
            df_stock = fetch_stock_data(ticker, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
        except ValueError:
            st.error(f"Data tidak ditemukan untuk ticker '{ticker}'. Ticker mungkin sudah delisting atau tidak tersedia di Yahoo Finance.")
            return
        except Exception as e:
            st.error(f"Gagal memuat data saham: {e}")
            return
            
        if df_stock.empty:
            st.error("Data saham tidak tersedia.")
            return
            
        df_tech = calculate_indicators(df_stock)
        latest = df_tech.iloc[-1]
        
        df_news = get_contextual_news(ticker)
        df_news_analyzed = analyze_news_dataframe(df_news, ticker)
        daily_sentiment = aggregate_daily_sentiment(df_news_analyzed, ticker)
        
        df_merged = merge_sentiment_with_stock(df_tech, daily_sentiment)
        pred_results = train_and_predict(df_merged)
        
        # Run short term scanner for this single stock
        avg_vol = df_tech["Volume"].tail(20).mean()
        fast_cand = [{
            "Ticker": ticker,
            "Price": latest["Close"],
            "Open": latest["Open"],
            "High": latest["High"],
            "Low": latest["Low"],
            "Prev_Close": df_tech.iloc[-2]["Close"],
            "Change_Pct": ((latest["Close"] - df_tech.iloc[-2]["Close"]) / df_tech.iloc[-2]["Close"]) * 100,
            "Volume": latest["Volume"],
            "Avg_Volume": avg_vol,
            "RVOL": latest["Volume"] / avg_vol if avg_vol > 0 else 1,
            "Trading_Value": latest["Close"] * latest["Volume"],
            "Vol_Trend": 1.0,
            "Vol_Consistency": 0.5,
            "Tradeability": 50,
            "df": df_stock
        }]
        scanner_res = run_deep_analysis(fast_cand, top_n=1, interval="1d")
        cand = scanner_res[0] if scanner_res else None
        
    st.markdown("---")
    
    # 1. Stock Analysis
    st.markdown("#### 1. Kondisi Harga (Technical)")
    price = latest['Close']
    st.write(f"- **Harga Terakhir:** Rp {price:,.0f}")
    st.write(f"- **RSI:** {latest.get('RSI', 50):.1f} " + 
             ("(Overbought)" if latest.get('RSI', 50) > 70 else "(Oversold)" if latest.get('RSI', 50) < 30 else "(Neutral)"))
    st.write(f"- **MACD:** {'Positive' if latest.get('MACD', 0) > latest.get('MACD_Signal', 0) else 'Negative'}")
    st.write(f"- **Skor Teknikal:** {get_technical_score(latest)}/5")
    
    # 2. News & External Factors
    st.markdown("#### 2. Berita & Sentimen Eksternal")
    if not df_news_analyzed.empty:
        impacts = df_news_analyzed['impact'].value_counts()
        st.write(f"- Ditemukan **{len(df_news_analyzed)}** berita/artikel relevan dalam beberapa waktu terakhir.")
        st.write(f"- Sentimen utama yang terpantau: **{df_news_analyzed.iloc[0]['impact']}** (berdasarkan relevansi industri/sektor).")
    else:
        st.write("- Tidak ada pergerakan berita signifikan yang terdeteksi.")
        
    # 3. Machine Learning Prediction & Target
    st.markdown("#### 3. Prediksi & Target (Short-Term Scanner)")
    if pred_results and pred_results["status"] == "success":
        horizons = pred_results.get("horizons", {})
        h_keys = list(horizons.keys())
        if len(h_keys) > 0:
            h1 = horizons.get(h_keys[0], {})
            h2 = horizons.get(h_keys[len(h_keys)//2], {}) if len(h_keys) > 2 else {}
            h3 = horizons.get(h_keys[-1], {}) if len(h_keys) > 1 else {}
            
            st.write(f"- **Terdekat (+{h_keys[0]}):** {h1.get('prediction')} ({h1.get('probability', 0)*100:.1f}% Prob) | Acc: {h1.get('accuracy', 0)*100:.1f}%")
            if h2:
                st.write(f"- **Menengah (+{h_keys[len(h_keys)//2]}):** {h2.get('prediction')} ({h2.get('probability', 0)*100:.1f}% Prob) | Acc: {h2.get('accuracy', 0)*100:.1f}%")
            if h3:
                st.write(f"- **Terjauh (+{h_keys[-1]}):** {h3.get('prediction')} ({h3.get('probability', 0)*100:.1f}% Prob) | Acc: {h3.get('accuracy', 0)*100:.1f}%")
                
            st.markdown("---")
            with st.expander("📊 Eksperimen Test Period (Training Configuration)"):
                st.markdown("Bandingkan pengaruh rasio pembagian data (Train/Test Split) terhadap performa model forecast.")
                
                exp_col1, exp_col2 = st.columns([1, 1])
                with exp_col1:
                    exp_split = st.select_slider(
                        "Test Period Split Ratio",
                        options=[0.5, 0.6, 0.7, 0.8, 0.9],
                        value=0.8,
                        format_func=lambda x: f"Train {int(x*100)}% / Test {int((1-x)*100)}%",
                        key="pres_split"
                    )
                with exp_col2:
                    st.write("")
                    st.write("")
                    run_exp = st.button("Jalankan Eksperimen & Lihat Hasil", key="pres_run")
                    
                if run_exp:
                    with st.spinner("Melatih ulang model untuk bereksperimen..."):
                        # Re-run train with new split
                        exp_results = train_and_predict(df_merged, ticker=f"{ticker}_1d", train_ratio=exp_split)
                        if exp_results["status"] == "success":
                            st.success("Eksperimen selesai!")
                            import pandas as pd
                            rows = []
                            for h_k, h_v in exp_results.get("horizons", {}).items():
                                rows.append({
                                    "Horizon": f"+{h_k}",
                                    "Akurasi Arah": f"{h_v.get('accuracy', 0):.1%}",
                                    "RMSE (Error)": f"Rp {h_v.get('rmse', 0):.0f}",
                                    "Prediksi Terakhir": h_v.get('prediction', 'N/A')
                                })
                            st.dataframe(pd.DataFrame(rows), use_container_width=True)
                        else:
                            st.error("Gagal menjalankan eksperimen.")
        
        if cand:
            entry = cand.get("Entry", {})
            tp = cand.get("Take_Profit", {})
            sl = cand.get("Stop_Loss", {})
            rr = cand.get("Risk_Reward", {})
            st.markdown("##### :material/ads_click: Strategi Transaksi (Scanner)")
            st.write(f"- **Skor Peluang Pendek:** {cand['Score']:.0f}/100")
            st.write(f"- **Area Beli:** Rp {entry.get('preferred_low', 0):,.0f} – Rp {entry.get('preferred_high', 0):,.0f}")
            st.write(f"- **Target Jual (TP1):** Rp {tp.get('tp1', 0):,.0f} (+{tp.get('tp1_pct', 0):.1f}%)")
            st.write(f"- **Batas Rugi (Stop Loss):** Rp {sl.get('price', 0):,.0f} (-{sl.get('loss_pct', 0):.1f}%)")
            st.write(f"- **Perbandingan Untung/Rugi:** {rr.get('display', 'N/A')}")
            
    else:
        st.write("- Prediksi AI sedang tidak tersedia untuk saham ini.")
        
    # 4. Kesimpulan & Risiko
    st.markdown("#### 4. Kesimpulan & Profil Risiko")
    if cand:
        st.info(get_scanner_explanation(cand))
        
        if cand.get("High_Risk"):
            for reason in cand.get("Risk_Reasons", []):
                st.error(f":material/warning: RISIKO TINGGI: {reason}")
            
        pa = cand.get("Price_Action", {})
        if "BREAKOUT" in pa.get("patterns", []):
            st.success(":material/check_circle: Terdeteksi potensi tembus atas (BREAKOUT).")
            
        sig = cand.get("Signal", {}).get("signal", "")
        if sig == "LONG_SETUP":
            st.success(f":material/check_circle: Sinyal: {sig}")
        elif "WATCH" in sig:
            st.warning(f":material/visibility: Sinyal: {sig}")
    else:
        pred = pred_results["today_prediction"] if pred_results else "UNKNOWN"
        prob = pred_results["probability"] if pred_results else 0
        tech_score = get_technical_score(latest)
        signal = generate_signal(tech_score, pred, prob)
        explanation = get_signal_explanation(signal, tech_score, pred, prob, 0.6)
        if signal == "BUY":
            st.success(explanation)
        elif signal == "SELL":
            st.error(explanation)
        else:
            st.warning(explanation)
            
    if not pred_results:
        st.warning("Data belum mencukupi untuk menghasilkan sinyal.")
