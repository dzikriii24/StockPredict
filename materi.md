
bisaa. kalau prompt sebelumnya fokusnya lebih ke **fitur teknis**, yang sekarang sebaiknya kita naikkan levelnya jadi **master prompt untuk menjelaskan keseluruhan sistem** — mulai dari tujuan project, alur data, AI/ML yang dipakai, setiap halaman, metode trading, sampai bagaimana semuanya nyambung ke **9 poin presentasi trading**.

aku bikin prompt-nya supaya AI yang membaca project/codebase kamu **nggak cuma menjelaskan UI**, tapi benar-benar membedah sistem dan menghasilkan dokumentasi yang bisa langsung dipakai buat **presentasi + demo kompetisi**.

---

# MASTER PROMPT — COMPLETE SYSTEM EXPLANATION & TRADING PRESENTATION MAPPING

> **Context:**
> Saya sedang mengembangkan sebuah **AI-Powered Stock Trading Analysis & Decision Support System** untuk analisis saham Indonesia (IDX/BEI).
>
> Sistem ini bukan sekadar dashboard saham, tetapi merupakan sebuah **end-to-end trading intelligence system** yang menggabungkan:
>
> * real-time / near-real-time market data
> * historical stock data
> * technical analysis
> * fundamental/market context jika data tersedia
> * sector analysis
> * financial news
> * news sentiment & event analysis
> * macroeconomic indicators
> * machine learning / AI prediction
> * short-term trading scanner
> * entry/exit analysis
> * take profit & stop loss
> * risk/reward analysis
> * historical backtesting
> * prediction accuracy evaluation
> * market timing analysis
> * presentation/reporting mode
>
> Tujuan utama sistem adalah membantu trader/investor memahami **kondisi pasar → memilih saham yang relevan → menganalisis saham → membuat trading setup → memperkirakan skenario harga → mengukur risiko → mengevaluasi hasil secara historis**.
>
> Sistem harus diposisikan sebagai **decision-support system**, bukan sistem yang menjamin keuntungan atau memberikan kepastian bahwa harga akan naik/turun.

---

# 1. JELASKAN PROJECT SECARA KESELURUHAN

Pertama, berikan penjelasan menyeluruh mengenai project ini.

Jelaskan:

### A. Apa project ini?

Jelaskan dalam bahasa yang mudah dipahami:

* nama/konsep sistem
* masalah yang ingin diselesaikan
* siapa pengguna sistem
* bagaimana sistem membantu proses trading
* mengapa sistem membutuhkan AI
* apa yang membedakan sistem ini dari dashboard saham biasa

Buat satu paragraf **project overview** yang bisa digunakan saat presentasi.

Contoh struktur:

```text
Market Data
     ↓
Data Processing
     ↓
Technical Analysis
     ↓
Market & Sector Analysis
     ↓
News & Event Analysis
     ↓
AI / Machine Learning
     ↓
Stock Screening
     ↓
Trading Setup
     ↓
Risk Analysis
     ↓
Backtesting
     ↓
Trading Decision Support
```

Jelaskan fungsi setiap tahap.

---

# 2. TUJUAN SISTEM

Jelaskan tujuan project secara teknis dan trading.

Pisahkan menjadi:

### Technical Objective

Contoh:

* mengintegrasikan data pasar
* melakukan preprocessing
* menghitung technical indicators
* membangun model machine learning
* melakukan multi-horizon forecasting
* melakukan backtesting
* membuat dashboard interaktif

### Trading Objective

Contoh:

* menemukan saham yang sedang memiliki momentum
* mengidentifikasi peluang short-term
* menentukan entry zone
* menentukan TP dan SL
* mengukur risk/reward
* memahami pengaruh berita terhadap saham
* mengevaluasi performa strategi secara historis

Jelaskan juga bahwa sistem **tidak bertujuan memprediksi pasar secara sempurna**.

---

# 3. ARSITEKTUR SISTEM

Jelaskan arsitektur keseluruhan project.

Buat diagram konseptual:

```text
                    ┌─────────────────────┐
                    │   MARKET DATA       │
                    │ OHLCV / Intraday    │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ DATA PROCESSING     │
                    │ Cleaning / Feature  │
                    │ Engineering         │
                    └──────────┬──────────┘
                               ↓
             ┌─────────────────┼─────────────────┐
             ↓                 ↓                 ↓
       TECHNICAL            NEWS             MACRO
       ANALYSIS             ANALYSIS         ANALYSIS
             ↓                 ↓                 ↓
             └─────────────────┼─────────────────┘
                               ↓
                    ┌─────────────────────┐
                    │ AI / ML ENGINE      │
                    │ Forecasting         │
                    │ Classification      │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ TRADING ENGINE      │
                    │ Signal / Entry      │
                    │ TP / SL / R:R       │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ BACKTESTING & RISK  │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ DASHBOARD            │
                    └─────────────────────┘
```

Jelaskan hubungan antar komponen tersebut.

---

# 4. DATA YANG DIGUNAKAN

Jelaskan seluruh sumber data yang digunakan sistem.

Kelompokkan menjadi:

### Market Data

* Open
* High
* Low
* Close
* Volume
* Trading Value
* Intraday data
* Market status
* VWAP jika tersedia/dihitung

### Historical Data

Jelaskan periode data:

```text
1 month
3 months
6 months
1 year
2 years
3 years
5 years
```

sesuai data yang benar-benar tersedia.

### News Data

Jelaskan:

* headline
* source
* publication time
* ticker/company
* sector
* industry
* keywords
* event
* sentiment
* relevance
* potential impact

### Macroeconomic Data

Jika tersedia:

* IHSG
* USD/IDR
* interest rate
* inflation
* gold
* crude oil
* commodity prices

Jelaskan bagaimana masing-masing data dapat digunakan sebagai feature/context.

**Jangan mengklaim data tersedia jika sebenarnya tidak tersedia di implementation.**

---

# 5. AI / MACHINE LEARNING YANG DIGUNAKAN

Ini bagian yang sangat penting.

Audit codebase dan jelaskan **AI/ML model yang benar-benar digunakan**, bukan model yang hanya direncanakan.

Untuk setiap model jelaskan:

```text
Model Name
Purpose
Input Features
Target
Training Data
Validation Method
Output
Evaluation Metrics
```

Contohnya jika implementation menggunakan:

### Random Forest

Jelaskan:

* mengapa digunakan
* feature yang digunakan
* target prediction
* output
* kelebihan
* keterbatasan

### XGBoost / Gradient Boosting

Jika digunakan, jelaskan:

* bagaimana model digunakan
* mengapa cocok untuk tabular financial features
* hyperparameter penting
* hasil validation

### LSTM / GRU

**Hanya jelaskan jika benar-benar digunakan.**

Jika tidak digunakan, jangan mengklaim bahwa sistem menggunakan LSTM.

---

# 6. FEATURE ENGINEERING

Jelaskan seluruh feature yang digunakan AI.

Kelompokkan:

### Price Features

* daily return
* log return
* price change
* volatility

### Moving Average

* SMA20
* SMA50
* EMA20
* EMA50

### Momentum

* RSI
* MACD
* ROC
* ADX

### Volatility

* ATR
* Bollinger Bands

### Volume

* volume
* average volume
* RVOL
* volume acceleration
* trading value

### Market Context

* IHSG return
* sector return
* USD/IDR
* commodity movement

### News Features

* sentiment score
* news volume
* relevance score
* event type
* impact score

Jelaskan **kenapa feature tersebut digunakan**.

---

# 7. AI FUTURE PRICE FORECAST

Jelaskan secara detail bagaimana sistem menghasilkan:

```text
CURRENT PRICE
       ↓
AI FORECAST
       ↓
+10m
+20m
+30m
+40m
+50m
+60m
```

Jika sistem mendukung horizon lain:

```text
1D
3D
5D
```

jelaskan juga.

Jelaskan:

* input model
* timeframe
* prediction horizon
* predicted price
* confidence / uncertainty
* lower bound
* upper bound
* bagaimana forecast ditampilkan pada chart

Forecast harus dipahami sebagai **model estimate**, bukan harga yang pasti terjadi.

---

# 8. HISTORICAL PREDICTION ACCURACY

Jelaskan bagaimana sistem menjawab pertanyaan:

> "Apakah prediksi AI sebelumnya benar?"

Sistem harus melakukan:

```text
Prediction at T
       ↓
Wait until T + Horizon
       ↓
Get Actual Price
       ↓
Compare
       ↓
Prediction Error
```

Jelaskan:

* MAE
* RMSE
* MAPE jika relevan
* directional accuracy
* prediction bias
* accuracy per horizon

Contoh:

```text
+10m → Directional Accuracy
+20m → Directional Accuracy
+30m → Directional Accuracy
+60m → Directional Accuracy
```

Jelaskan juga bagaimana **walk-forward validation** digunakan agar historical prediction tidak menggunakan informasi masa depan.

---

# 9. 6 FITUR UTAMA DASHBOARD

Jelaskan secara mendalam enam halaman utama berikut.

---

## A. LIVE MARKET CENTER

Jelaskan halaman ini sebagai **pusat kondisi pasar saat ini**.

Isi:

* market status
* last update
* data source
* realtime/delayed status
* IHSG
* market breadth
* advancing stocks
* declining stocks
* unchanged stocks
* volume
* trading value
* top gainers
* top losers
* most active
* most volatile
* sector performance
* market sentiment
* market regime

Jelaskan bagaimana halaman ini menjawab:

> **"Sekarang kondisi pasar sedang seperti apa?"**

Tambahkan real-time monitoring:

```text
WebSocket / Streaming Data
        ↓
Tick
        ↓
Current Candle Update
        ↓
Indicator Update
        ↓
Dashboard Update
```

Jika provider tidak menyediakan real-time data, sistem **harus menampilkan status delayed**, bukan berpura-pura realtime.

---

# B. DAFTAR SEMUA SAHAM

Jelaskan halaman yang berisi seluruh saham Indonesia yang masuk universe sistem.

Table minimal:

```text
Ticker
Company
Sector
Price
Change
Volume
RVOL
RSI
Trend
Technical Score
News Activity
News Sentiment
AI Forecast
Prediction Accuracy
Short-Term Score
Signal
```

Tambahkan filter:

* sector
* industry
* price
* market cap jika tersedia
* volume
* volatility
* RSI
* trend
* news
* AI forecast
* score
* liquidity

Jelaskan bagaimana halaman ini menjadi **universe saham sebelum masuk ke scanner**.

---

# C. PETA SEKTOR INDUSTRI

Jelaskan halaman ini sebagai **sector intelligence layer**.

Tampilkan:

* sektor
* jumlah saham
* average return
* advance ratio
* sector momentum
* volume
* volatility
* technical score
* news activity
* sentiment
* market impact

Gunakan:

* heatmap
* treemap
* sector ranking secara deskriptif
* sector performance chart

Jelaskan bagaimana user dapat mengetahui:

> "Sektor mana yang sedang aktif dan bagaimana kondisi saham-saham di dalamnya?"

Jangan membuat ranking "sektor terbaik" jika sistem tidak memiliki metodologi yang jelas. Gunakan metrik aktual.

---

# D. PEMINDAI JANGKA PENDEK

Ini adalah salah satu fitur utama project.

Jelaskan bahwa scanner ditujukan untuk menemukan **setup short-term 1–5 trading days**, bukan menjamin saham yang akan menghasilkan profit terbesar.

Pipeline:

```text
ALL STOCKS
    ↓
Liquidity Filter
    ↓
Volume Analysis
    ↓
Momentum
    ↓
Technical Setup
    ↓
News Catalyst
    ↓
Market Context
    ↓
AI Forecast
    ↓
Risk / Reward
    ↓
SHORT-TERM SCORE
```

Analisis:

* price momentum
* volume
* RVOL
* VWAP
* RSI
* MACD
* EMA
* ADX
* ATR
* support
* resistance
* breakout
* pullback
* rebound
* consolidation
* news catalyst
* sector momentum
* AI forecast

Output:

```text
Ticker
Setup
Entry Zone
Current Price
TP1
TP2
Stop Loss
Risk/Reward
AI Forecast
Forecast Range
Prediction Accuracy
Short-Term Score
Risk Level
```

Tambahkan:

### WHY THIS STOCK?

Jelaskan alasan berdasarkan data aktual:

```text
Technical:
Volume meningkat
Price above VWAP
RSI menunjukkan momentum

News:
Terdapat event relevan terhadap sektor

Market:
Sektor sedang mengalami peningkatan aktivitas

AI:
Model memproyeksikan kenaikan pada horizon tertentu
```

Jangan menggunakan kalimat:

> "pasti naik"

atau

> "dijamin profit".

---

# E. ANALISIS SAHAM MENDALAM

Ini adalah halaman untuk melakukan **deep analysis terhadap satu saham**.

Struktur:

### 1. Overview

* company
* sector
* industry
* current price
* daily change
* volume
* liquidity

### 2. Technical Analysis

* candlestick
* MA
* EMA
* RSI
* MACD
* Bollinger Bands
* VWAP
* support
* resistance
* volume

### 3. AI Prediction

* actual historical price
* historical prediction
* prediction accuracy
* future forecast
* +10m
* +20m
* +30m
* +40m
* +50m
* +60m

### 4. News & Event Analysis

Untuk setiap berita:

```text
Headline
Source
Time
Sector
Event
Relevance
Sentiment
Impact
Confidence
Why It Matters
```

### 5. Market Context

* IHSG
* sector
* commodity
* USD/IDR
* macro

### 6. Trading Setup

```text
Entry
TP1
TP2
SL
Risk/Reward
Holding Horizon
Setup Type
```

### 7. Risk Analysis

* volatility
* ATR
* drawdown
* liquidity
* uncertainty
* prediction error

---

# F. MODE PRESENTASI

Buat halaman khusus yang mengubah hasil analisis sistem menjadi **alur presentasi trading**.

Mode ini harus langsung mengikuti struktur:

```text
1. LATAR BELAKANG
2. TUJUAN
3. DASAR TEORI TRADING
4. ANALISIS SAHAM
5. ANALISIS TRANSAKSIONAL
6. TEKNIKAL TRADING
7. PREDIKSI HASIL TRANSAKSI
8. TARGET TRANSAKSI
9. KESIMPULAN & REKOMENDASI
```

Jelaskan isi setiap slide.

---

# 10. HUBUNGKAN SYSTEM DENGAN 9 POIN PRESENTASI TRADING

Buat mapping yang sangat jelas:

| Presentasi               | Fitur Sistem                                  |
| ------------------------ | --------------------------------------------- |
| Latar Belakang           | Market Problem + Live Market Center           |
| Tujuan                   | System Objective                              |
| Dasar Teori Trading      | Technical Analysis + Risk Management          |
| Analisis Saham           | All Stocks + Sector Map + Deep Analysis       |
| Analisis Transaksional   | Trading Setup + Volume + VWAP + Market Timing |
| Teknikal Trading         | RSI + MACD + MA + VWAP + Support/Resistance   |
| Prediksi Hasil           | AI Future Forecast + Backtesting              |
| Target Transaksi         | Entry + TP + SL + Risk/Reward                 |
| Kesimpulan & Rekomendasi | Presentation Mode + AI/Technical/News Summary |

Tetapi jangan hanya membuat tabel.

Untuk setiap poin jelaskan:

**apa yang ditampilkan → data yang digunakan → metode yang digunakan → output yang dihasilkan → bagaimana digunakan dalam trading analysis.**

---

# 11. ANALISIS TRANSAKSIONAL

Jelaskan secara khusus bagaimana sistem menentukan **rencana transaksi**.

Contoh:

```text
Market Condition
      ↓
Stock Selection
      ↓
Setup Detection
      ↓
Entry Zone
      ↓
Stop Loss
      ↓
Take Profit
      ↓
Risk/Reward
      ↓
Position Size
      ↓
Trade Plan
```

Jelaskan bagaimana:

* entry ditentukan
* stop loss ditentukan
* take profit ditentukan
* risk/reward dihitung
* position sizing dihitung
* maksimum risiko ditentukan

---

# 12. TEKNIKAL TRADING YANG DIGUNAKAN

Buat penjelasan teori + implementasi.

Minimal:

### Moving Average

Apa fungsi dan bagaimana digunakan.

### RSI

Apa yang diukur dan bagaimana digunakan.

### MACD

Bagaimana momentum/trend dianalisis.

### VWAP

Mengapa penting untuk short-term trading.

### Support & Resistance

Bagaimana level ditentukan.

### Volume & RVOL

Bagaimana volume digunakan untuk validasi momentum.

### ATR

Bagaimana volatility digunakan untuk SL/TP.

### Price Action

Breakout, pullback, rebound, consolidation.

Jelaskan **bukan hanya definisi indikator**, tetapi bagaimana indikator tersebut masuk ke decision engine.

---

# 13. TRADING SIGNAL ENGINE

Jelaskan bagaimana sistem menggabungkan berbagai komponen.

Contoh:

```text
Technical Score
      +
Volume Score
      +
Momentum Score
      +
News Score
      +
Sector Score
      +
Market Score
      +
AI Forecast
      +
Risk/Reward
      ↓
Trading Context
```

Jika implementation menggunakan weighted score, tampilkan formula sebenarnya.

Jika tidak ada formula, jangan membuat formula fiktif.

Output dapat berupa:

```text
LONG SETUP
WAIT
BREAKOUT WATCH
PULLBACK WATCH
NO TRADE
HIGH RISK
```

atau label lain yang memang ada di implementation.

Jelaskan bahwa:

> **AI prediction ≠ trading signal**

Contoh:

```text
AI Forecast: UP
Technical: Weak
Volume: Low
Resistance: Near
Risk/Reward: Poor

→ WAIT
```

---

# 14. BACKTESTING

Jelaskan bagaimana sistem mengevaluasi strategi menggunakan data historis.

Bandingkan:

### Strategy A

Technical strategy

### Strategy B

AI prediction strategy

### Strategy C

Technical + AI

### Strategy D

Technical + AI + News + Market Context

Jika memang tersedia.

Metrics:

* total return
* win rate
* number of trades
* profit factor
* max drawdown
* Sharpe Ratio jika digunakan
* average trade
* average holding period

Bandingkan juga dengan:

**Buy & Hold benchmark.**

Jelaskan bahwa backtest harus memasukkan:

* transaction fee
* slippage
* realistic execution
* no look-ahead bias
* chronological train/test split

---

# 15. HISTORICAL MARKET TIMING

Jelaskan bagaimana sistem menentukan waktu trading berdasarkan data historis.

Analisis:

```text
09:00
09:10
09:20
...
15:50
```

atau interval yang tersedia.

Bandingkan:

* average return
* win rate
* volatility
* volume
* breakout frequency
* reversal frequency
* sample size

Jangan hardcode:

> "waktu terbaik adalah 15:45"

Waktu yang ditampilkan harus berasal dari **historical data analysis**.

---

# 16. NEWS & EVENT INTELLIGENCE

Jelaskan bahwa sistem tidak hanya melakukan sentiment analysis.

Pipeline:

```text
NEWS
 ↓
RELEVANCE
 ↓
EVENT DETECTION
 ↓
BUSINESS EXPOSURE
 ↓
POTENTIAL IMPACT
 ↓
CONFIDENCE
```

Contoh:

```text
AALI
↓
Sector: Agriculture
↓
Event: Forest Fire
↓
Business Exposure: Plantation
↓
Potential Impact: Mixed / Negative / Uncertain
```

Jelaskan mengapa:

> **bad news ≠ automatically stock goes down**

dan

> **positive sentiment ≠ automatically stock goes up**

News digunakan sebagai **context/catalyst**, bukan sebagai satu-satunya dasar trading decision.

---

# 17. EXPLAINABILITY

Sistem harus mampu menjawab:

> **"Kenapa sistem menghasilkan analisis seperti ini?"**

Buat:

### WHY THIS STOCK?

### WHY THIS SIGNAL?

### WHY THIS ENTRY?

### WHY THIS TARGET?

### WHAT ARE THE RISKS?

Jawaban harus berdasarkan data aktual.

Struktur:

```text
TECHNICAL
NEWS
MARKET
SECTOR
AI
RISK
```

Pisahkan:

```text
FACT
ANALYSIS
MODEL PREDICTION
UNCERTAINTY
```

---

# 18. TEKNOLOGI YANG DIGUNAKAN

Audit seluruh project dan jelaskan tech stack:

### Frontend

Misalnya:

* React
* Vite
* Tailwind
* Streamlit jika digunakan
* Lightweight Charts

### Backend

Misalnya:

* Python
* FastAPI
* Node.js
* Express

### Database

Misalnya:

* PostgreSQL
* Supabase
* MySQL
* SQLite

### AI/ML

Misalnya:

* Scikit-learn
* XGBoost
* PyTorch
* TensorFlow

### Data Source

Jelaskan API/provider sebenarnya.

### News

Misalnya:

* NewsAPI

### Deployment

Jelaskan platform yang benar-benar digunakan.

**Jangan mengarang technology yang tidak ada di codebase.**

---

# 19. ALUR DATA REAL-TIME

Jelaskan bagaimana data bergerak dari provider hingga dashboard.

```text
Market Data Provider
        ↓
API / WebSocket
        ↓
Data Ingestion
        ↓
Data Validation
        ↓
Feature Calculation
        ↓
Technical Indicators
        ↓
AI Inference
        ↓
Signal Engine
        ↓
Dashboard
```

Jelaskan perbedaan:

### Historical Data

digunakan untuk:

* training
* validation
* backtesting
* historical analysis

### Real-Time Data

digunakan untuk:

* current price
* current candle
* live volume
* current indicators
* live scanner
* current forecast

Jika provider sebenarnya delayed:

```text
DATA STATUS: DELAYED
```

dan jangan menyebutnya realtime.

---

# 20. DATABASE / MODEL MEMORY

Jika sistem menyimpan historical predictions, jelaskan struktur datanya.

Minimal:

```text
ticker
timestamp
timeframe
model_version
horizon
predicted_price
lower_bound
upper_bound
actual_price
error
direction_predicted
direction_actual
correct
```

Tujuannya agar sistem bisa menjawab:

> "Bagaimana performa AI selama ini?"

bukan hanya menghasilkan prediction tanpa evaluasi.

---

# 21. UI / USER EXPERIENCE

Jelaskan dashboard sebagai satu workflow:

```text
LIVE MARKET CENTER
        ↓
DAFTAR SEMUA SAHAM
        ↓
PETA SEKTOR
        ↓
PEMINDAI JANGKA PENDEK
        ↓
ANALISIS SAHAM MENDALAM
        ↓
TRADING PLAN
        ↓
BACKTEST
        ↓
MODE PRESENTASI
```

Desain harus terlihat seperti:

**professional financial analytics terminal**

bukan generic AI SaaS.

Hindari:

* excessive gradients
* neon colors
* glowing cards
* random AI illustrations
* terlalu banyak rounded cards
* dekorasi yang tidak memiliki fungsi

Prioritaskan:

* typography
* hierarchy
* whitespace
* data density
* chart readability
* professional financial UI
* dark/light mode
* green/red hanya untuk market movement.

---

# 22. OUTPUT AKHIR UNTUK PRESENTASI

Setelah melakukan audit project, buat **narasi presentasi lengkap** berdasarkan implementasi aktual.

Struktur:

## Slide 1 — Latar Belakang

Masalah yang dihadapi trader:

* data tersebar
* market bergerak cepat
* sulit menggabungkan technical + news + market context
* sulit mengevaluasi prediksi
* sulit menentukan risk/reward

Lalu jelaskan solusi sistem.

---

## Slide 2 — Tujuan

Jelaskan tujuan sistem.

---

## Slide 3 — Dasar Teori Trading

Jelaskan:

* trend
* momentum
* volatility
* volume
* support/resistance
* risk/reward
* technical indicators
* machine learning forecasting

---

## Slide 4 — Analisis Saham

Gunakan:

**Daftar Semua Saham → Peta Sektor → Analisis Saham Mendalam**

---

## Slide 5 — Analisis Transaksional

Tampilkan:

```text
Current Price
Entry
TP1
TP2
SL
Risk/Reward
Position Size
Holding Horizon
```

---

## Slide 6 — Teknikal Trading

Tampilkan chart:

* Candlestick
* MA/EMA
* VWAP
* RSI
* MACD
* Volume
* Support/Resistance

---

## Slide 7 — Prediksi Hasil Transaksi

Tampilkan:

```text
Actual Price
Historical Prediction
AI Future Forecast
+10m
+20m
+30m
+40m
+50m
+60m
```

Tambahkan:

**Historical Prediction Accuracy**

agar bisa menjawab apakah prediksi sebelumnya memang sesuai dengan actual price.

---

## Slide 8 — Target Transaksi

Tampilkan:

```text
Entry
TP1
TP2
Stop Loss
Risk/Reward
Potential Return
Potential Loss
```

Jelaskan sumber setiap level.

---

## Slide 9 — Kesimpulan & Rekomendasi

Jangan hanya mengatakan:

> BUY STOCK X

Tetapi buat kesimpulan berbasis evidence:

```text
Market Condition
+
Sector Condition
+
Technical Setup
+
News/Event
+
AI Forecast
+
Historical Model Performance
+
Risk/Reward
=
Trading Context
```

Kemudian tampilkan:

**Opportunity**

**Risk**

**Uncertainty**

**Trade Plan**

---

# 23. FINAL SYSTEM SUMMARY

Terakhir, buat satu penjelasan singkat yang menjawab:

> **"Sebenarnya project ini apa?"**

Format:

```text
PROJECT
↓
AI-Powered Stock Trading Intelligence System

INPUT
↓
Market Data
Historical Data
News
Macro
Sector Data

PROCESS
↓
Technical Analysis
Feature Engineering
AI/ML Prediction
News/Event Analysis
Market Analysis
Risk Analysis

OUTPUT
↓
Stock Screening
Sector Intelligence
Future Forecast
Trading Setup
Entry / TP / SL
Risk/Reward
Backtesting
Prediction Accuracy

INTERFACE
↓
Live Market Center
All Stocks
Sector Map
Short-Term Scanner
Deep Stock Analysis
Presentation Mode
```

Buat **project explanation**, **technical explanation**, dan **trading explanation** secara terpisah sehingga saya bisa menggunakannya untuk:

1. memahami sistem,
2. menjelaskan sistem kepada juri,
3. membuat slide presentasi,
4. melakukan demo aplikasi,
5. menjawab pertanyaan teknis juri,
6. menjelaskan AI/ML yang digunakan,
7. menjelaskan dasar pengambilan keputusan trading.

### IMPORTANT FINAL RULE

**Jangan mengarang fitur, model, dataset, API, metric, atau hasil performa.**

Audit implementation/codebase terlebih dahulu.

Jika sebuah fitur masih berupa planned feature tetapi belum benar-benar implemented, tandai:

> `PLANNED / NOT YET IMPLEMENTED`

Jika sebuah data tidak tersedia secara realtime, tandai:

> `DELAYED / LAST AVAILABLE`

Jika model belum pernah diuji secara out-of-sample, jangan menyebutnya sebagai model yang terbukti akurat.

Tujuan utama dokumentasi ini adalah menghasilkan **gambaran yang benar-benar sesuai dengan sistem yang dibangun**, sekaligus menghubungkan seluruh fitur teknis dengan **9 bagian presentasi trading** di atas.
