Upgrade project **Stock Trading Analysis & Prediction System** yang sudah dibuat sebelumnya.

JANGAN membuat project baru dari awal.

Pertahankan seluruh fitur yang sudah ada:

* Yahoo Finance / yfinance
* OHLCV
* Technical Indicators
* Stock Screener
* Random Forest
* Prediction UP/DOWN
* Trading Signal
* Entry / Target / Stop Loss
* Risk/Reward
* Backtesting
* Portfolio Simulation
* Plotly Charts
* Streamlit Dashboard

Sekarang tambahkan **External Market Intelligence Layer** yang menghubungkan:

1. Financial News
2. News Sentiment Analysis
3. Macroeconomic Indicators
4. Market Context

Tujuan upgrade ini adalah membuat sistem tidak hanya melihat historical price dan technical indicators, tetapi juga mempertimbangkan informasi eksternal yang secara potensial berkaitan dengan pergerakan pasar.

---

# 1. NEW SYSTEM ARCHITECTURE

Upgrade pipeline menjadi:

```text
Historical Stock Data
        │
        ├───────────────┐
        ↓               ↓
Technical Analysis   Market Data
        │               │
        │          IHSG / USD-IDR
        │               │
        └───────┬───────┘
                ↓
        External Features
                ↑
                │
        Financial News
                ↓
        Sentiment Analysis
                ↓
      Daily Sentiment Score
                │
                ↓
        Feature Engineering
                ↓
        Machine Learning
                ↓
        UP / DOWN Prediction
                ↓
        Trading Signal
                ↓
      Transaction Simulation
                ↓
        Backtesting & Risk
```

---

# 2. FINANCIAL NEWS DATA

Tambahkan modul:

```text
src/news_loader.py
```

Gunakan financial news API yang memiliki data berita pasar dan entity/ticker.

Prioritaskan API yang menyediakan:

* headline
* description/summary
* publication date
* source
* related ticker/entity
* URL

Buat konfigurasi API menggunakan environment variable.

Jangan hardcode API key.

Gunakan:

```text
NEWS_API_KEY
```

di `.env`.

Tambahkan `.env.example`.

Jika API key belum tersedia, aplikasi tetap harus bisa berjalan menggunakan historical/cached news dataset atau menampilkan pesan yang jelas bahwa fitur news membutuhkan API key.

Jangan membuat aplikasi crash hanya karena API news tidak tersedia.

---

# 3. NEWS-TICKER MAPPING

Sistem harus mencoba menghubungkan berita dengan saham tertentu.

Contoh:

```text
BBCA → Bank Central Asia
BBRI → Bank Rakyat Indonesia
BMRI → Bank Mandiri
TLKM → Telkom Indonesia
ASII → Astra International
```

Buat konfigurasi mapping ticker → company name.

Jika API menyediakan entity/ticker langsung, prioritaskan entity tersebut.

Jika tidak tersedia, gunakan keyword/company-name matching sebagai fallback.

---

# 4. SENTIMENT ANALYSIS

Tambahkan modul:

```text
src/sentiment.py
```

Lakukan sentiment analysis terhadap headline/summary berita.

Target sentiment:

```text
POSITIVE
NEUTRAL
NEGATIVE
```

Tambahkan numerical sentiment score:

```text
positive → +1
neutral  →  0
negative → -1
```

Jika model menghasilkan confidence/probability, simpan juga:

```text
sentiment_confidence
```

Prioritaskan pendekatan yang cocok untuk bahasa berita.

Jika berita berbahasa Indonesia, gunakan model NLP berbahasa Indonesia seperti IndoBERT atau model sentiment Indonesia yang sesuai.

Jika implementasi transformer terlalu berat untuk environment lokal, sediakan fallback sentiment model yang lebih ringan.

Jelaskan di README model sentiment yang digunakan.

---

# 5. DAILY SENTIMENT AGGREGATION

Agregasikan berita berdasarkan tanggal dan ticker.

Untuk setiap ticker dan tanggal hitung:

```text
news_count
positive_count
neutral_count
negative_count
positive_ratio
negative_ratio
average_sentiment
weighted_sentiment
```

Contoh:

```text
Date        Ticker   News   Avg Sentiment

2026-09-10  BBCA     12       +0.32
2026-09-11  BBCA      8       -0.18
2026-09-12  BBCA     15       +0.41
```

Tambahkan rolling sentiment:

```text
Sentiment MA3
Sentiment MA7
```

---

# 6. NEWS MOMENTUM

Tambahkan feature:

```text
News Volume
News Volume Change
Sentiment Change
Sentiment Momentum
```

Tujuannya untuk mengetahui apakah perhatian pasar terhadap suatu saham meningkat atau menurun.

Contoh:

```text
News Volume ↑
+
Positive Sentiment ↑
=
Positive News Momentum
```

Jangan mengubah kombinasi ini menjadi klaim bahwa harga pasti naik.

Gunakan sebagai model feature.

---

# 7. MACROECONOMIC FEATURES

Tambahkan modul:

```text
src/macro_data.py
```

Tambahkan beberapa market/macro indicators yang tersedia secara reliable.

Prioritaskan:

1. IHSG / market index
2. USD/IDR
3. US market index jika data tersedia
4. Gold
5. Oil

Jika data BI Rate atau inflasi tersedia secara reliable melalui public source, tambahkan:

* BI Rate
* Indonesia inflation

Pastikan setiap macro variable memiliki:

```text
date
value
daily/monthly change
```

Untuk data bulanan seperti inflasi, lakukan proper forward filling sesuai metodologi time-series dan dokumentasikan metode tersebut.

Jangan menggunakan informasi masa depan.

---

# 8. MARKET CONTEXT FEATURES

Tambahkan:

```text
IHSG Daily Return
USDIDR Daily Return
Gold Return
Oil Return
Market Volatility
```

Untuk setiap saham tambahkan:

```text
Stock Return
Market Return
Relative Strength
```

Contoh:

```text
Relative Strength =
Stock Return - IHSG Return
```

---

# 9. EXTENDED MACHINE LEARNING FEATURES

Model yang sebelumnya menggunakan:

```text
MA20
MA50
RSI
MACD
Volume
Volatility
```

sekarang tambahkan:

```text
News Count
Average Sentiment
Sentiment MA3
Sentiment MA7
News Momentum
IHSG Return
USDIDR Return
Gold Return
Oil Return
Relative Strength
```

Sehingga model memiliki tiga kategori feature:

```text
TECHNICAL FEATURES
+
NEWS/SENTIMENT FEATURES
+
MACRO/MARKET FEATURES
```

---

# 10. MODEL COMPARISON

Ini adalah fitur yang sangat penting.

Jangan hanya menggunakan satu model.

Buat dua eksperimen:

### Model A — Technical Only

Features:

```text
OHLCV
MA
RSI
MACD
Bollinger Bands
Volume
Volatility
```

### Model B — Technical + External

Features:

```text
Technical Features
+
News Sentiment
+
News Momentum
+
Macro Features
+
Market Features
```

Kemudian bandingkan:

```text
                    Technical Only
                    vs
                    Technical + News + Macro
```

Gunakan metrik:

* Accuracy
* Precision
* Recall
* F1
* ROC-AUC jika relevan
* Directional Accuracy

Untuk trading/backtesting:

* Total Return
* Win Rate
* Maximum Drawdown
* Profit Factor
* Number of Trades

Tujuannya adalah mengetahui apakah external information memberikan tambahan informasi pada dataset yang digunakan.

JANGAN mengasumsikan model dengan sentiment pasti lebih baik.

---

# 11. ABLATION ANALYSIS

Tambahkan opsi eksperimen:

```text
A. Technical Only

B. Technical + News

C. Technical + Macro

D. Technical + News + Macro
```

Tampilkan tabel:

```text
Model                 Accuracy    F1    Return    Drawdown

Technical Only          ...       ...    ...        ...

Technical + News        ...       ...    ...        ...

Technical + Macro       ...       ...    ...        ...

All Features            ...       ...    ...        ...
```

Gunakan hasil aktual dari dataset.

Jangan mengarang angka.

---

# 12. NEWS DASHBOARD

Tambahkan tab:

```text
[News & Sentiment]
```

Tampilkan:

### Latest News

```text
Headline
Source
Date
Ticker
Sentiment
Sentiment Score
```

### Sentiment Trend

Plotly line chart:

```text
Sentiment Score vs Date
```

### News Volume

Bar chart:

```text
News Count vs Date
```

### Sentiment Distribution

Donut/bar chart:

```text
Positive
Neutral
Negative
```

---

# 13. MACRO DASHBOARD

Tambahkan tab:

```text
[Market & Macro]
```

Tampilkan:

```text
IHSG
USD/IDR
Gold
Oil
```

dengan:

* current/latest value
* daily change
* historical chart

Tambahkan market context:

```text
Market Trend
Market Return
Volatility
```

---

# 14. ENHANCED STOCK DETAIL PAGE

Pada halaman detail saham, tampilkan:

```text
==========================================

BBCA.JK

PRICE
TECHNICAL
NEWS
MACRO
PREDICTION
TRADING PLAN

==========================================
```

Tambahkan section:

### Technical Context

```text
Trend
RSI
MACD
MA20
MA50
Volume
```

### News Context

```text
News Count
Average Sentiment
Sentiment Trend
Latest Relevant News
```

### Market Context

```text
IHSG Return
USD/IDR Return
Gold Return
Oil Return
```

### ML Prediction

```text
Prediction
Probability UP
Probability DOWN
```

### Trading Signal

```text
BUY / HOLD / SELL
```

---

# 15. ENHANCED PREDICTION EXPLANATION

Tambahkan feature importance dari Random Forest.

Gunakan:

```text
Feature Importance
```

Tampilkan chart horizontal bar.

Contoh:

```text
RSI                  ██████████
MACD                 ████████
Sentiment            ███████
MA20                 ██████
IHSG Return          █████
Volume Ratio         ████
USDIDR Return        ███
```

Gunakan hasil aktual model.

Jangan mengarang feature importance.

Tujuannya agar user dapat menjelaskan:

> "Model tidak hanya menghasilkan prediksi, tetapi juga menunjukkan feature apa yang paling berkontribusi terhadap keputusan model."

---

# 16. EVENT / ISSUE DETECTION

Tambahkan fitur sederhana untuk mendeteksi lonjakan berita.

Jika:

```text
News Count hari ini > rolling mean + threshold
```

tandai sebagai:

```text
HIGH NEWS ACTIVITY
```

Jika sentiment berubah drastis:

```text
Sentiment Change < threshold
```

tandai:

```text
SENTIMENT SHIFT
```

Contoh dashboard:

```text
⚠ HIGH NEWS ACTIVITY

BBCA memiliki peningkatan jumlah berita
dibandingkan rata-rata periode sebelumnya.

Dominant Sentiment:
NEGATIVE

Average Sentiment:
-0.42
```

Gunakan bahasa netral dan jangan menyimpulkan bahwa kondisi tersebut pasti menyebabkan harga turun.

---

# 17. IMPORTANT TIME ALIGNMENT

Ini sangat penting untuk mencegah data leakage.

Berita hanya boleh digunakan jika berita tersebut sudah tersedia SEBELUM waktu prediksi.

Contoh:

```text
Market Date: 2026-09-15

News published:
2026-09-15 09:00 → boleh digunakan
2026-09-15 12:00 → boleh digunakan
2026-09-16 10:00 → TIDAK boleh digunakan
```

Jika hanya menggunakan daily prediction, dokumentasikan timezone dan cut-off time.

Jangan menggunakan berita yang baru muncul setelah target prediction period.

---

# 18. DATA QUALITY

Tambahkan validation:

* duplicate news removal
* duplicate headlines
* missing timestamp
* missing ticker
* invalid sentiment
* timezone normalization
* stale macro data
* future data leakage

Log semua proses preprocessing.

---

# 19. DASHBOARD SUMMARY

Upgrade halaman Overview menjadi:

```text
STOCK TRADING ANALYSIS

Price
Technical Score
News Sentiment
Market Context
ML Prediction
Trading Signal
Risk/Reward
```

Tambahkan visual summary:

```text
Technical        🟢 Bullish
News Sentiment   🟡 Neutral
Market Context   🟢 Positive
ML Prediction    🟢 UP
```

Gunakan label tersebut hanya sebagai hasil rule/data yang sudah ditentukan, bukan sebagai klaim kepastian arah harga.

---

# 20. PRESENTATION SUPPORT

Tambahkan section:

```text
Why This Signal?
```

Generate explanation berdasarkan actual features.

Contoh format:

```text
Technical:
Price is above MA20 and MA50.

Momentum:
RSI is in the neutral range and MACD is positive.

News:
Recent news sentiment is neutral-positive.

Market:
IHSG return is positive during the observation period.

Model:
Random Forest predicts UP with probability X%.
```

Jangan membuat narasi yang tidak didukung data.

---

# 21. PRESENTATION MAPPING

Pastikan dashboard secara eksplisit membantu menjawab:

### 4. ANALISIS SAHAM

Gunakan:

* price chart
* technical indicators
* news sentiment
* macro context
* support/resistance
* volume

### 5. ANALISIS TRANSAKSIONAL

Gunakan:

* entry
* target
* stop loss
* position sizing
* risk/reward
* trading signal

### 6. TEKNIKAL TRADING

Gunakan:

* MA
* RSI
* MACD
* Bollinger Bands
* Volume
* trading rules

### 7. PREDIKSI HASIL TRANSAKSI

Gunakan:

* ML prediction
* prediction probability
* backtesting
* model comparison
* technical vs external features

### 8. TARGET HASIL TRANSAKSI

Gunakan:

* target price
* stop loss
* potential return
* risk/reward
* historical backtest results

### 9. KESIMPULAN

Gunakan:

* technical context
* sentiment context
* macro context
* model result
* backtest result
* limitations

---

# 22. RESEARCH-STYLE COMPARISON

Tambahkan halaman:

```text
[Model Experiment]
```

Dengan tujuan menunjukkan:

```text
Does adding news and macro data provide
additional predictive information?
```

Bandingkan:

```text
Technical Only
        vs
Technical + News
        vs
Technical + Macro
        vs
Technical + News + Macro
```

Gunakan dataset dan periode testing yang sama untuk seluruh model.

Gunakan chronological split yang sama.

Jangan memilih model berdasarkan hasil test setelah melihat hasilnya secara berulang tanpa dokumentasi.

---

# 23. README UPDATE

Tambahkan dokumentasi:

1. External data sources
2. News API
3. Sentiment model
4. Macro data
5. Feature engineering
6. Time alignment
7. Leakage prevention
8. Model comparison
9. Limitations

Jelaskan bahwa hubungan antara news, macroeconomic variables, sentiment, dan stock movement bersifat kompleks dan tidak berarti setiap berita akan menyebabkan pergerakan harga tertentu.

---

# 24. FINAL OUTPUT

Setelah upgrade selesai, project harus menghasilkan:

```text
PRICE ANALYSIS
+
TECHNICAL ANALYSIS
+
NEWS ANALYSIS
+
SENTIMENT ANALYSIS
+
MACRO ANALYSIS
+
MACHINE LEARNING
+
TRADING SIGNAL
+
TRANSACTION PLAN
+
BACKTESTING
+
RISK ANALYSIS
```

Tujuan akhirnya adalah membuat sistem yang dapat digunakan sebagai **educational stock trading analysis dashboard**, bukan sistem yang mengklaim dapat memastikan arah harga saham.

Pastikan seluruh fitur lama tetap berfungsi setelah upgrade.

Jalankan test terhadap seluruh pipeline dan pastikan aplikasi tetap dapat dijalankan dengan:

```bash
streamlit run app.py
```
