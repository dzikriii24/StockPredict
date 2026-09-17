# 📈 Stock Trading Analysis & Prediction System v2.0

Sistem analisis dan simulasi trading saham Indonesia komprehensif yang menggabungkan **Technical Analysis**, **External Market Intelligence (Berita & Makroekonomi)**, **Machine Learning Prediction**, dan **Backtesting** dalam satu dashboard interaktif.

> ⚠️ **Disclaimer:** Project ini dibuat untuk keperluan **edukasi dan penelitian akademis**. Bukan rekomendasi investasi. Past performance does not guarantee future results.

---

## 🎯 Features Update (v2.0)

1. **Market Intelligence Layer** — Integrasi Berita Finansial & Sentimen Analysis (TextBlob)
2. **Macroeconomic Data** — IHSG, USD/IDR, Gold, & Crude Oil impact analysis
3. **ML Experiment / Ablation Study** — Perbandingan akurasi model teknikal vs teknikal+sentimen vs All Features
4. **Screener & Ranking** — Bandingkan dan urutkan berbagai saham berdasarkan peluang teknikal.
5. **⚡ Short-Term Market Scanner** — Pemindai canggih untuk menemukan peluang *swing trading* jangka pendek (1-5 hari) yang dilengkapi dengan sistem peringatan *breakout* dan filter likuiditas tinggi.
6. **Expanded Tickers** — Coverage saham diperluas menjadi ~90 saham (LQ45 & IDX30)
7. **Dashboard UI V2** — Tampilan tab baru untuk eksperimentasi model, sentimen, dan makro.

---

## 🏗️ Architecture

```text
stock-predict/
├── app.py                    # Streamlit main dashboard v2
├── requirements.txt          # Python dependencies
├── README.md                 # Documentation
├── .env.example              # API Key templates
│
├── data/                     # Cached data & models (auto-generated)
├── models/                   # Saved ML models (auto-generated)
│
├── src/
│   ├── __init__.py
│   ├── data_loader.py        # Yahoo Finance data & 90+ Ticker Config
│   ├── news_loader.py        # Feed RSS/YFinance News Loader (No API Key required)
│   ├── macro_data.py         # Macroeconomic indicators loader
│   ├── sentiment.py          # Sentiment Analysis with TextBlob
│   ├── preprocessing.py      # Data cleaning & feature engineering
│   ├── indicators.py         # Technical indicators calculation
│   ├── screener.py           # Multi-stock screening & ranking
│   ├── short_term_scanner.py # ⚡ Short-Term Market Scanner & ML scoring
│   ├── prediction.py         # Random Forest ML model & Ablation experiments
│   ├── trading_strategy.py   # Signal generation & trade planning
│   ├── backtesting.py        # Historical backtesting engine
│   ├── risk_analysis.py      # Risk metrics & position sizing
│   └── visualization.py      # Plotly interactive charts (Technical & Sentiment)
```

---

## 🚀 Installation & Running

### Prerequisites
- Python 3.10+
- Koneksi internet (untuk download data saham & RSS Feed)

### Setup

```bash
# 1. Clone & masuk ke folder
cd stock-predict

# 2. Setup environment variables (Optional untuk NewsAPI)
copy .env.example .env

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run dashboard
streamlit run app.py
```

Dashboard akan terbuka di browser pada `http://localhost:8501`.

---

## 📊 Data Source & Coverage

- **Historical Stock & Macro Data:** Yahoo Finance (`yfinance`)
- **News Data:** RSS Feeds & Yahoo Finance News.
- **Coverage:** ~90 Saham Indonesia teratas (Perbankan, Energi, Konsumer, Tech, dll).

---

## 🤖 Machine Learning Experiments

Sistem kini mendukung **Ablation Study (Eksperimen Fitur)** untuk melihat pengaruh data eksternal terhadap akurasi ML:
- **Model A:** Technical Only
- **Model B:** Technical + News Sentiment
- **Model C:** Technical + Macroeconomic Data
- **Model D:** All Features

### Model
- **Algorithm:** Random Forest Classifier (200 trees, Max Depth 10)
- **Target:** 1 (Harga hari berikutnya NAIK), 0 (Harga hari berikutnya TURUN)
- **Split Data:** **Chronological split** (80/20) — mencegah data leakage masa depan.
- **Evaluasi:** Accuracy, Precision, Recall, F1 Score, ROC-AUC.

---

## 💹 Trading Strategy

### Signal Generation Rules

| Signal | Kondisi |
|--------|---------|
| **BUY** | Technical Score ≥ 4 AND Prediction = UP AND Prob UP ≥ threshold |
| **SELL** | Prediction = DOWN AND Prob DOWN ≥ threshold |
| **HOLD** | Tidak memenuhi kondisi BUY atau SELL |

### Technical Scoring (Max 5)
```
MA20 > MA50             → +1
Price > MA20            → +1
RSI between 30-70       → +1
MACD > Signal Line      → +1
Volume Ratio > 1        → +1
```

---

## 🛠️ Fitur ⚡ Short-Term Market Scanner

Fitur terbaru yang dirancang untuk memindai pasar (80+ saham teratas) guna menemukan peluang *swing trading* (1-5 hari perdagangan).

**Alur Kerja Scanner:**
1. **Fast Scan (Filter Likuiditas):** Memindai semua saham, mengabaikan saham tidak likuid atau data kosong.
2. **Deep Analysis:** Mengambil Top 20-30 kandidat, menjalankan indikator teknikal penuh, sentimen berita, dan melatih model Machine Learning pada saat itu juga.
3. **Short-Term Score (0-100):** Dihitung berdasarkan: Momentum Teknikal (25%), Likuiditas/Volume (20%), Tren Harga (15%), Berita (15%), Model AI (10%), dan Rasio Risk/Reward (15%).
4. **Target Calculation:** Menghitung Potensi Entry, Target Price (berdasarkan AI/ATR), dan Stop Loss ideal.

> **PENAFIAN PENTING (DISCLAIMER):**
> Sistem tidak memberikan **jaminan profit**, tidak menjamin harga pasti akan menyentuh target, dan tidak memastikan bahwa *score* tertinggi akan selalu menguntungkan. Pemindai ini adalah alat bantu analisis (Analytical Ranking), bukan dukun atau *financial advisor*. Risiko sepenuhnya berada di tangan pengguna.

---

## ⚠️ Limitations

1. **Historical performance** tidak menjamin future performance
2. **TextBlob Sentiment** terbatas pada bahasa Inggris, terjemahan ke berita lokal mungkin kurang akurat (namun efisien tanpa API Key berbayar).
3. **ML predictions** mengandung ketidakpastian.
4. Project ini untuk **edukasi/penelitian akademis**, BUKAN rekomendasi investasi

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **Streamlit** — Dashboard framework
- **Plotly** — Interactive charts
- **scikit-learn** — Machine learning
- **yfinance** — Financial Data
- **TextBlob & feedparser** — NLP Sentiment & News Extraction
- **pandas & numpy** — Data processing
