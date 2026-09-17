
Buatkan sebuah project end-to-end bernama **Stock Trading Analysis & Prediction System** untuk kebutuhan tugas kuliah dan presentasi trading saham.

### TUJUAN PROJECT

Project ini bukan hanya untuk memprediksi harga saham, tetapi menjadi sistem analisis dan simulasi trading yang menggabungkan:

1. Historical Stock Data
2. Technical Analysis
3. Stock Screening
4. Machine Learning Prediction
5. Trading Signal Generation
6. Transaction Analysis
7. Backtesting
8. Risk & Reward Analysis
9. Portfolio Simulation
10. Interactive Dashboard

Sistem harus membantu menghasilkan informasi yang dapat digunakan untuk memenuhi materi presentasi:

* 4. Analisis Saham
* 5. Analisis Transaksional Saham
* 6. Teknikal Trading Saham yang Akan Dilakukan
* 7. Prediksi Hasil Transaksi Saham yang Akan Dilakukan
* 8. Target Hasil Transaksi Saham
* 9. Kesimpulan dan Rekomendasi

---

# 1. DATA SOURCE

Gunakan data historical saham dari Yahoo Finance melalui Python library `yfinance`.

Gunakan ticker saham Indonesia dengan suffix `.JK`, misalnya:

* BBCA.JK
* BBRI.JK
* BMRI.JK
* TLKM.JK
* ASII.JK
* ICBP.JK
* GOTO.JK
* ANTM.JK
* INDF.JK
* UNVR.JK

Jangan menggunakan data sintetis jika historical data tersedia.

Sediakan konfigurasi agar user dapat:

* memilih satu saham
* memilih beberapa saham
* menentukan start date
* menentukan end date
* menentukan interval data

Default gunakan data harian.

Buat error handling apabila ticker tidak ditemukan, data kosong, atau koneksi gagal.

---

# 2. PROJECT ARCHITECTURE

Gunakan Python sebagai core data analysis dan machine learning.

Jika membuat dashboard, gunakan **Streamlit** agar project mudah dijalankan secara lokal dan mudah dipresentasikan.

Struktur project yang rapi:

```text
stock-trading-system/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│
├── models/
│
├── src/
│   ├── data_loader.py
│   ├── preprocessing.py
│   ├── indicators.py
│   ├── screener.py
│   ├── prediction.py
│   ├── trading_strategy.py
│   ├── backtesting.py
│   ├── risk_analysis.py
│   └── visualization.py
│
└── notebooks/
    └── analysis.ipynb
```

Pisahkan logic data, indicator calculation, machine learning, trading strategy, backtesting, dan visualization.

---

# 3. DATA PREPROCESSING

Gunakan historical OHLCV:

* Open
* High
* Low
* Close
* Volume

Lakukan:

* missing value handling
* sorting berdasarkan date
* duplicate removal
* valid numeric conversion

Tambahkan feature:

* Daily Return
* High-Low Percentage
* Close-Open Percentage
* Rolling Volatility

Jangan melakukan data leakage.

---

# 4. TECHNICAL ANALYSIS

Hitung indikator teknikal berikut:

### Moving Average

* MA20
* MA50

### RSI

Gunakan periode 14.

### MACD

Gunakan konfigurasi standar:

* fast = 12
* slow = 26
* signal = 9

### Bollinger Bands

Gunakan:

* SMA20
* Upper Band
* Lower Band

### Volume

Tambahkan:

* Volume MA20
* Volume Ratio

### Support & Resistance

Implementasikan metode sederhana berbasis historical rolling high/low.

Jelaskan pada UI bagaimana masing-masing indikator digunakan.

---

# 5. STOCK SCREENING

Buat fitur **Stock Screener** untuk membandingkan beberapa saham.

Untuk setiap saham tampilkan:

* ticker
* latest price
* daily return
* MA20
* MA50
* RSI
* MACD
* volume ratio
* trend
* technical score
* ML prediction
* prediction probability
* suggested signal

Buat sistem scoring yang TRANSPARAN.

Contoh:

```text
MA20 > MA50             +1
Price > MA20            +1
RSI 30–70               +1
MACD > Signal           +1
Volume Ratio > 1        +1
```

Technical score maksimum = 5.

Jangan menyebut saham sebagai "pasti naik". Gunakan istilah:

* Bullish
* Neutral
* Bearish
* Candidate for further analysis

Jangan memberikan klaim investasi yang pasti.

---

# 6. MACHINE LEARNING PREDICTION

Gunakan **Random Forest Classifier** sebagai baseline model.

Tujuan model:

Memprediksi arah harga pada periode berikutnya.

Target:

```text
1 = harga periode berikutnya naik
0 = harga periode berikutnya turun
```

Feature model:

* MA20
* MA50
* RSI
* MACD
* MACD Signal
* Bollinger Upper
* Bollinger Lower
* Volume Ratio
* Daily Return
* Volatility

Gunakan chronological train/test split.

Contoh:

```text
Training : 2023–2025
Testing  : 2026
```

JANGAN menggunakan random train-test split karena data merupakan time series.

Tambahkan:

* Accuracy
* Precision
* Recall
* F1 Score
* Confusion Matrix

Tampilkan hasil evaluasi model.

---

# 7. PREDICTION OUTPUT

Untuk saham yang dipilih, tampilkan:

```text
Ticker
Current Price
Prediction
Probability UP
Probability DOWN
```

Contoh UI:

```text
BBCA.JK

Current Price: Rp8.500

Prediction: UP

Probability:
UP   72%
DOWN 28%
```

Gunakan probability sebagai confidence model, bukan sebagai probabilitas pasti bahwa saham akan naik.

---

# 8. TRADING SIGNAL

Gabungkan technical analysis dan machine learning.

Buat rule-based trading signal.

Contoh:

BUY apabila:

* technical score >= 4
* model prediction = UP
* probability UP >= threshold

SELL apabila:

* model prediction = DOWN
* probability DOWN >= threshold

HOLD apabila kondisi belum memenuhi BUY atau SELL.

Threshold harus configurable.

Jangan menggunakan kata "jaminan profit".

---

# 9. TRANSACTION ANALYSIS

Untuk setiap kandidat transaksi tampilkan:

* Entry Price
* Target Price
* Stop Loss
* Position Size
* Risk per Share
* Potential Profit
* Potential Loss
* Risk/Reward Ratio

Gunakan risk management yang configurable.

Contoh:

```text
Capital = Rp10.000.000

Entry = Rp8.500
Target = Rp9.000
Stop Loss = Rp8.250
```

Hitung otomatis:

```text
Potential Profit
Potential Loss
Risk/Reward Ratio
```

Position sizing harus mempertimbangkan maximum risk per trade.

Default:

```text
Risk per trade = 2% of capital
```

Tampilkan perhitungannya secara transparan.

---

# 10. BACKTESTING

Buat simple historical backtesting engine.

Strategi:

* generate BUY / HOLD / SELL berdasarkan rules
* simulate entry
* simulate exit berdasarkan target / stop loss / opposite signal
* hitung profit/loss

Tampilkan:

* Initial Capital
* Final Capital
* Total Return
* Number of Trades
* Winning Trades
* Losing Trades
* Win Rate
* Average Profit
* Average Loss
* Maximum Drawdown
* Profit Factor

Sertakan transaction cost configurable agar hasil lebih realistis.

---

# 11. BUY & HOLD COMPARISON

Bandingkan strategi model dengan strategi sederhana:

```text
Strategy A:
ML + Technical Trading Strategy

Strategy B:
Buy & Hold
```

Tampilkan:

* cumulative return
* equity curve
* maximum drawdown

Tujuannya bukan untuk menyatakan strategi tertentu pasti lebih baik, tetapi menunjukkan bagaimana performa historis kedua pendekatan pada periode pengujian.

---

# 12. VISUALIZATION

Gunakan Plotly untuk interactive charts.

Minimal sediakan:

### Chart 1 — Candlestick

Tampilkan:

* Open
* High
* Low
* Close

Overlay:

* MA20
* MA50

### Chart 2 — Volume

Bar chart volume + Volume MA20.

### Chart 3 — RSI

Tampilkan RSI dengan garis:

* 30
* 70

### Chart 4 — MACD

Tampilkan:

* MACD
* Signal
* Histogram

### Chart 5 — Bollinger Bands

Tampilkan:

* Close
* Upper Band
* Lower Band

### Chart 6 — Prediction

Visualisasikan:

* actual price
* predicted direction
* buy signal
* sell signal

### Chart 7 — Equity Curve

Bandingkan:

* Trading Strategy
* Buy & Hold

### Chart 8 — Drawdown

Tampilkan historical drawdown.

---

# 13. DASHBOARD

Buat Streamlit dashboard dengan sidebar:

```text
Stock Trading Analysis System

Sidebar:

Stock:
[BBCA.JK ▼]

Date Range:
[Start] [End]

Initial Capital:
[Rp10.000.000]

Risk per Trade:
[2%]

Prediction Threshold:
[70%]
```

Main page:

```text
================================================

BBCA.JK
Stock Trading Analysis & Prediction

Current Price
Rp8.500

Daily Change
+1.2%

Prediction
↑ UP

Probability UP
72%

Technical Score
4 / 5

Signal
BUY

================================================
```

Kemudian tabs:

```text
[Overview]
[Technical Analysis]
[Prediction]
[Trading Plan]
[Backtesting]
[Risk Analysis]
[Stock Screener]
```

---

# 14. OVERVIEW PAGE

Tampilkan ringkasan yang bisa langsung digunakan untuk presentasi.

Contoh:

```text
Current Price
Trend
Technical Score
ML Prediction
Prediction Probability
Trading Signal
Entry Price
Target Price
Stop Loss
Risk/Reward
```

Tambahkan automatic textual insight berdasarkan data aktual.

Contoh:

```text
Technical Insight:

Harga saat ini berada di atas MA20 dan MA50.
RSI berada pada area netral.
MACD menunjukkan momentum positif.
Model Random Forest memprediksi arah UP dengan probability 72%.

Trading Plan:

Entry: ...
Target: ...
Stop Loss: ...
Risk/Reward: ...
```

Jangan menghasilkan klaim seperti "harga pasti naik".

---

# 15. STOCK SCREENING PAGE

Buat tabel sortable.

Contoh:

```text
Ticker | Price | RSI | MA Trend | MACD | Score | ML Prediction | Probability | Signal
```

User dapat memilih saham dari hasil screening untuk masuk ke detail analysis.

---

# 16. TRADING PLAN

Tampilkan satu proposed simulated trade:

```text
Stock: BBCA.JK

Signal: BUY

Entry Price: Rp...
Target Price: Rp...
Stop Loss: Rp...

Capital:
Rp10.000.000

Position Size:
...

Potential Profit:
...

Potential Loss:
...

Risk/Reward:
1 : ...
```

Berikan label yang jelas bahwa ini adalah **simulasi berdasarkan historical/model output**, bukan rekomendasi investasi personal.

---

# 17. PRESENTATION REPORT

Buat fitur yang otomatis menghasilkan summary untuk kebutuhan presentasi.

Summary harus menjawab:

### 4. Analisis Saham

* kondisi trend
* technical indicators
* volume
* support/resistance
* technical score

### 5. Analisis Transaksional Saham

* alasan entry
* entry price
* position size
* exit condition
* stop loss

### 6. Teknikal Trading Saham

* indikator yang digunakan
* rule trading
* ML model
* signal generation

### 7. Prediksi Hasil Transaksi

* model prediction
* probability
* historical backtest
* expected scenario

### 8. Target Hasil Transaksi

* target price
* potential profit
* maximum loss
* risk/reward
* target return

### 9. Kesimpulan

* kondisi saham berdasarkan data
* hasil model
* hasil backtesting
* risk
* limitations

---

# 18. IMPORTANT: MODEL LIMITATIONS

Tambahkan bagian khusus:

```text
Model Limitations
```

Jelaskan bahwa:

* historical performance tidak menjamin future performance
* stock prices are affected by external events
* technical indicators are not guaranteed signals
* machine learning predictions contain uncertainty
* transaction costs can affect actual returns
* model can suffer from regime changes
* this project is for educational/research purposes

---

# 19. UI/UX

Buat dashboard modern, clean, professional, dan cocok untuk presentasi mahasiswa IT.

Gunakan:

* dark/light theme yang nyaman
* cards untuk KPI
* interactive Plotly charts
* responsive layout
* clear tables
* tooltips untuk istilah financial/technical

Jangan membuat UI terlalu ramai.

---

# 20. CODE QUALITY

Pastikan:

* modular
* readable
* comments pada bagian penting
* type hints jika memungkinkan
* error handling
* requirements.txt
* README lengkap
* `.gitignore`
* tidak hardcode API key
* reproducible

Buat seluruh source code yang runnable.

---

# 21. README

README harus menjelaskan:

1. Project overview
2. Features
3. Architecture
4. Installation
5. Running locally
6. Data source
7. Technical indicators
8. Machine learning methodology
9. Trading strategy
10. Backtesting methodology
11. Evaluation metrics
12. Limitations
13. Educational disclaimer

---

# 22. FINAL REQUIREMENT

Project harus dapat dijalankan dengan:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Pastikan tidak ada placeholder yang membuat project tidak dapat dijalankan.

Jika terdapat keputusan desain yang belum ditentukan, pilih solusi yang paling sederhana, reproducible, dan cocok untuk proyek kuliah.

Prioritaskan functional MVP terlebih dahulu, kemudian visualization dan UI.

Jangan membuat sistem yang hanya menghasilkan angka prediksi. Sistem harus menghubungkan:

DATA → ANALYSIS → PREDICTION → SIGNAL → TRANSACTION PLAN → BACKTEST → PERFORMANCE → PRESENTATION INSIGHT.

Setelah selesai, jelaskan:

1. Struktur project
2. Cara menjalankan
3. Cara kerja setiap modul
4. Cara membaca dashboard
5. Cara menggunakan hasilnya untuk presentasi poin 4–9
6. Contoh alur satu transaksi dari signal sampai backtesting
7. Keterbatasan sistem
