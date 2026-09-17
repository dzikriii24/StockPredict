# MASTER PROMPT — COMPLETE SYSTEM EXPLANATION & TRADING PRESENTATION MAPPING

---

## 1. JELASKAN PROJECT SECARA KESELURUHAN

### A. Apa project ini?

Sistem ini adalah **AI-Powered Stock Trading Analysis & Decision Support System** yang dirancang khusus untuk menganalisis saham-saham di Bursa Efek Indonesia (IDX). Sistem ini bukan sekadar dashboard harga, melainkan *end-to-end trading intelligence system* yang menggabungkan data pasar historis dan intraday, analisis teknikal komprehensif, sentimen berita, dan data makroekonomi untuk memberikan rekomendasi perdagangan jangka pendek berbasis Machine Learning. Sistem ini ditujukan untuk trader dan investor yang membutuhkan panduan objektif berbasis data (data-driven) dalam memilih saham berpotensi, menentukan titik *entry/exit*, dan mengelola risiko, bukan untuk menjamin keuntungan pasti.

**Project Overview:**

```text
Market Data (yfinance)
     ↓
Data Processing (Cleaning & Feature Engineering)
     ↓
Technical Analysis (Indicators: MA, RSI, MACD, dll)
     ↓
Market & Sector Analysis
     ↓
News & Event Analysis (News Sentiment)
     ↓
AI / Machine Learning (Random Forest Classifier & Regressor)
     ↓
Stock Screening (Short-Term Scanner)
     ↓
Trading Setup (Entry, TP1, TP2, SL)
     ↓
Risk Analysis (Risk/Reward, Volatility)
     ↓
Backtesting
     ↓
Trading Decision Support (Dashboard)
```

---

## 2. TUJUAN SISTEM

### Technical Objective

- Mengintegrasikan data pasar historis dan intraday (1m, 5m, 15m, 1h, 1d) secara otomatis dari `yfinance`.
- Melakukan *preprocessing* dan ekstraksi puluhan fitur teknikal, sentimen berita, dan makroekonomi.
- Membangun model machine learning (Random Forest) untuk memprediksi arah harga dan nilai harga masa depan (Multi-horizon forecasting).
- Menyediakan *backtesting* secara kronologis (*no look-ahead bias*) untuk mengevaluasi strategi.
- Membangun antarmuka interaktif yang profesional menggunakan Streamlit.

### Trading Objective

- Menemukan saham-saham likuid dengan momentum jangka pendek (1–5 hari atau intraday).
- Menentukan zona *entry* yang optimal berdasarkan indikator pendukung (seperti VWAP dan Support/Resistance).
- Menentukan target *Take Profit* (TP) dan *Stop Loss* (SL) berdasarkan volatilitas (ATR).
- Menghitung rasio *Risk/Reward* untuk memvalidasi apakah setup perdagangan layak dieksekusi.
- Mengevaluasi performa prediksi AI secara historis untuk mengetahui tingkat keandalannya.

*(Catatan: Sistem tidak bertujuan memprediksi pasar secara sempurna, melainkan sebagai asisten pengambil keputusan).*

---

## 3. ARSITEKTUR SISTEM

```text
                    ┌─────────────────────┐
                    │   MARKET DATA       │
                    │ yfinance (OHLCV)    │
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
       (MA, RSI, dll)   (Sentiment/Count) (IHSG, USD/IDR)
             ↓                 ↓                 ↓
             └─────────────────┼─────────────────┘
                               ↓
                    ┌─────────────────────┐
                    │ AI / ML ENGINE      │
                    │ Random Forest       │
                    │ (Classifier & Regr) │
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
                    │ STREAMLIT DASHBOARD │
                    └─────────────────────┘
```

---

## 4. DATA YANG DIGUNAKAN

### Market Data

Data diunduh menggunakan `yfinance`.

- Open, High, Low, Close, Volume
- Intraday data (1m, 5m, 15m, 30m, 1h)
- Daily data (1d)
- VWAP (Volume Weighted Average Price) dihitung dari OHLCV

### Historical Data

Periode data historis secara default di-set maksimal 3 tahun terakhir untuk data harian, dan disesuaikan batasan yfinance untuk intraday (misal 7 hari untuk 1m).

### News Data

- Sentimen berita rata-rata (*average_sentiment*)
- Volume berita (*news_count*)
- Momentum sentimen
- *Sentiment Moving Averages* (MA3, MA7)

### Macroeconomic Data

- IHSG Return
- USD/IDR Return
- Harga Emas (*Gold_Return*)
- Harga Minyak (*Oil_Return*)
- Relative Strength

---

## 5. AI / MACHINE LEARNING YANG DIGUNAKAN

Sistem menggunakan ansambel Machine Learning dari library `scikit-learn`.

### Random Forest Classifier & Regressor

- **Purpose**: Memprediksi arah pergerakan harga selanjutnya (Classifier) dan estimasi titik harga (Regressor).
- **Input Features**: Dibagi menjadi 4 model komparasi:
  - Model A: Technical Only (MA, RSI, MACD, BB, Volume, Volatility)
  - Model B: Technical + News
  - Model C: Technical + Macro
  - Model D: Technical + News + Macro (All Features)
- **Target**:
  - Classifier: `1` jika *Close* masa depan > *Close* saat ini, `0` jika sebaliknya.
  - Regressor: Nilai *Close* aktual pada horizon masa depan.
- **Training Data**: Split kronologis, tidak *random* (contoh: 80% data awal untuk *train*, 20% data akhir untuk *test*). Tidak ada informasi masa depan yang bocor (*no look-ahead bias*).
- **Output**:
  - Classifier: `UP` atau `DOWN` beserta probabilitasnya.
  - Regressor: Prediksi harga masa depan.
- **Evaluation Metrics**: Accuracy, Precision, Recall, F1-Score, ROC-AUC, dan RMSE (untuk regresi).

---

## 6. FEATURE ENGINEERING

### Price Features

- *Daily Return*
- *Volatility*

### Moving Average & Trend

- *SMA20, SMA50*
- *EMA9, EMA20, EMA50*

### Momentum

- *RSI* (Relative Strength Index)
- *MACD, MACD Signal, MACD Hist*
- *ROC* (Rate of Change)
- *Stochastic K & D*
- *ADX* (Average Directional Index)

### Volatility

- *ATR* (Average True Range)
- *Bollinger Bands* (Upper, Middle, Lower)

### Volume & Liquidity

- *Volume_MA20*
- *Volume_Ratio* (Current Volume / Volume_MA20)
- *VWAP*

### Market Context & News (Jika tersedia)

- *IHSG_Return, USDIDR_Return, Gold_Return, Oil_Return*
- *news_count, average_sentiment, sentiment_momentum*

**Kenapa feature tersebut digunakan?**
Kombinasi fitur ini memberikan konteks menyeluruh tentang likuiditas (Volume), momentum pergerakan saat ini (RSI, MACD), batasan volatilitas ekstrem (Bollinger, ATR), serta pengaruh sentimen eksternal (Makro/Berita) untuk *decision tree* pada Random Forest.

---

## 7. AI FUTURE PRICE FORECAST

Sistem melakukan proyeksi pergerakan (multi-horizon forecast) secara dinamis tergantung *timeframe* data:

```text
CURRENT PRICE
       ↓
AI FORECAST (Random Forest)
       ↓
(Untuk data 1m)
+10m → Prediksi arah & harga
+20m → Prediksi arah & harga
+30m → Prediksi arah & harga
+40m → Prediksi arah & harga
+50m → Prediksi arah & harga
+60m → Prediksi arah & harga

(Untuk data 1d)
+1D → Prediksi arah & harga
+5D → Prediksi arah & harga
+20D → Prediksi arah & harga
```

**Detail:**

- **Confidence/Uncertainty**: Menghasilkan probabilitas (misal 65% UP) dan menghitung *Upper/Lower bound* batas atas/bawah berbasis metrik RMSE dari model yang telah dilatih (Multiplier 1.96 untuk ~95% confidence).
- *Forecast* ini ditampilkan pada chart sebagai batas estimasi pergerakan, bukan jaminan kepastian.

---

## 8. HISTORICAL PREDICTION ACCURACY

Sistem mengevaluasi prediksi historis model menggunakan *walk-forward validation* (chronological split).

```text
Prediction at T (menggunakan data 80% masa lalu)
       ↓
Wait until T + Horizon (data 20% akhir / test set)
       ↓
Get Actual Price
       ↓
Compare Target vs Predicted
       ↓
Prediction Error / Accuracy
```

- **Metrics**: Akurasi arah (*directional accuracy* dalam persentase), F1-Score, dan RMSE (selisih nilai prediksi dengan nilai aktual).
- Melalui tabel metrik yang jelas, user bisa menjawab **"Apakah model sebelumnya memprediksi pergerakan saham ini dengan akurat di test set?"**

---

## 9. 6 FITUR UTAMA DASHBOARD

### A. LIVE MARKET CENTER

Pusat kondisi pasar (*Market Overview*).

- Menampilkan data pergerakan indeks atau saham unggulan.
- Karena menggunakan API gratis (*yfinance*), data berstatus `DELAYED / LAST AVAILABLE` tergantung bursa dan tidak murni websocket tick-by-tick real-time.

### B. DAFTAR SEMUA SAHAM

Tabel utama *universe* saham. Menampilkan seluruh *ticker* (seperti `BBCA.JK`, `GOTO.JK`, dsb) lengkap dengan harga saat ini, perubahan, sektor, metrik teknikal dasar (RSI, MA), serta Technical Score (0-5). Berfungsi sebagai filter awal sebelum *screening*.

### C. PETA SEKTOR INDUSTRI

Menganalisis performa berdasarkan Sektor (Banking, Telco, Consumer, Mining, dll). Memberikan informasi sentimen per sektor: apakah uang sedang mengalir ke saham Bank atau ke saham Komoditas?

### D. PEMINDAI JANGKA PENDEK (SCANNER)

Alat untuk menemukan setup trading.

- Melakukan filter likuiditas dan tren.
- Menghasilkan **Trading Setup**: Entry Zone, TP1, TP2, Stop Loss (SL), dan Risk/Reward ratio (R:R).
- Menjelaskan sentimen: Kenapa saham ini terpilih? (Berdasarkan *Technical Score*, volume, kondisi *oversold/overbought*).

### E. ANALISIS SAHAM MENDALAM

Halaman khusus (*Deep Stock Analysis*) untuk membedah satu saham secara detail.

- **Chart Analisis**: Candlestick + MA + VWAP + BB.
- **AI Prediction**: Tabel prediksi *multi-horizon* (misal +1d, +5d) beserta probabilitas naik/turun dan tingkat akurasi historis.
- **Trading Plan**: Rekomendasi Titik Entry, TP, SL, dan Risk.

### F. MODE PRESENTASI

Mengubah hasil *deep analysis* saham menjadi susunan slide presentasi (Latar Belakang hingga Kesimpulan) secara otomatis. Dirancang khusus untuk mempresentasikan hasil temuan analisis ke dewan juri atau komite investasi.

---

## 10. HUBUNGKAN SYSTEM DENGAN 9 POIN PRESENTASI TRADING

| Poin Presentasi                    | Fitur Sistem                       | Detail Penggunaan                                                                                                         |
| ---------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Latar Belakang**           | Live Market Center                 | Menampilkan urgensi kondisi pasar secara makro (apakah sedang*bullish* atau *bearish*).                               |
| **Tujuan**                   | Konsep Decision Support            | Menegaskan bahwa ini adalah sistem asisten*data-driven*, bukan pencetak *sure-win*.                                   |
| **Dasar Teori Trading**      | Modul Indikator (MA, RSI, VWAP)    | Memadukan teori volatilitas dan tren dalam sebuah perhitungan skoring yang objektif.                                      |
| **Analisis Saham**           | Daftar Semua Saham & Peta Sektor   | Proses pemilihan (*screening*) dari *universe* IDX ke saham incaran berdasarkan sektor.                               |
| **Analisis Transaksional**   | Short-Term Scanner (Trading Setup) | Kalkulasi*entry/exit* dengan pendekatan *Risk/Reward*.                                                                |
| **Teknikal Trading**         | Deep Analysis (Chart & Indicators) | Pembacaan momentum RSI, MACD, dan validasi dengan*Volume Ratio*.                                                        |
| **Prediksi Hasil**           | AI Future Forecast                 | Menggunakan Random Forest untuk memproyeksi target dan memberikan batas keyakinan (*bounds*).                           |
| **Target Transaksi**         | Risk Analysis / ATR                | Penggunaan nilai ukur volatilitas (ATR) untuk meletakkan TP dan SL secara dinamis, bukan tebak-tebakan.                   |
| **Kesimpulan & Rekomendasi** | Mode Presentasi                    | Integrasi skor teknikal, probabilitas AI, dan parameter R:R menjadi satu kesimpulan:*BUY*, *WAIT*, atau *NO TRADE*. |

---

## 11. ANALISIS TRANSAKSIONAL (TRADING PLAN ENGINE)

Sistem menghasilkan rencana transaksi melalui pipeline:

```text
Market Condition → Stock Selection (Scanner) → Technical Score > threshold
      ↓
Entry Zone: Ditetapkan dekat harga penutupan terakhir (jika momentum valid) atau area VWAP/Support terdekat.
      ↓
Stop Loss: Dihitung menggunakan multiplier dari Volatilitas (ATR), misal: Entry - (1.5 * ATR).
      ↓
Take Profit: Dihitung berdasarkan kelipatan ATR ke atas atau Resistance terdekat (TP1 & TP2).
      ↓
Risk/Reward (R:R): (Target Profit - Entry) / (Entry - Stop Loss).
      ↓
Trade Plan: Mengembalikan status apakah R:R cukup ideal (misal > 1.5).
```

---

## 12. TEKNIKAL TRADING YANG DIGUNAKAN

- **Moving Average (SMA/EMA)**: EMA9/20/50 digunakan sebagai *baseline* tren. Jika Harga > MA20 dan MA20 > MA50 = Tren Positif.
- **RSI**: Mengukur *overbought* (>70) dan *oversold* (<30). Disertakan dalam *Technical Score*.
- **MACD**: Histogram positif digunakan untuk mendeteksi momentum awal pergerakan harga.
- **VWAP**: Sebagai alat ukur *fair value* rata-rata intraday/jangka pendek untuk zona pantulan (*rebound*).
- **Bollinger Bands**: Mengidentifikasi titik ekstrem (menjauhi *upper/lower band*).
- **ATR**: Indikator utama pengukur volatilitas untuk meletakkan level *Stop Loss* yang rasional.
- **Volume Ratio**: Perbandingan volume hari ini dengan rata-rata MA20 Volume. Jika > 1.0, pergerakan divalidasi oleh tingginya minat pasar.

---

## 13. TRADING SIGNAL ENGINE

Sistem **tidak** sekadar menggunakan tebakan AI sebagai sinyal final.

```text
Technical Score (MA, RSI, MACD, Volume)
       +
AI Forecast Probability (>60%)
       +
Risk/Reward Ratio (Tolerable)
       ↓
Trading Context
```

Sistem memberi skoring (Technical Score 0-5). AI hanya bertindak sebagai **Konfirmator**.

> **AI prediction ≠ trading signal**
> Jika AI memprediksi `UP` tetapi sentimen harga berada di bawah VWAP dan MA, sistem akan memberi pandangan teknikal yang lemah (*Wait* atau *High Risk*).

---

## 14. BACKTESTING

Modul `backtesting.py` memungkinkan simulasi performa dari prediksi sistem dibandingkan dengan strategi murni *Buy & Hold*.

- **Metrik Backtest**: *Total Return*, *Win Rate*, *Number of Trades*, *Max Drawdown*, dan *Profit Factor*.
- Backtest bersifat realistis: Hanya masuk posisi jika *Target* klasifikasi ML mengarah ke atas, dieksekusi secara kronologis tanpa *look-ahead bias*.

---

## 15. HISTORICAL MARKET TIMING

Sistem mendukung ekstraksi pola *intraday timing*. Melalui penggunaan interval data intraday (1m, 5m, 15m), pengguna dapat menganalisis kapan suatu saham sering mengalami lonjakan volatilitas (misal: sering *breakout* di jam 09:15 - 09:30). Modul `historical_timing.py` mengakumulasi rerata probabilitas arah dan *return* berdasarkan jam dan hari.

---

## 16. NEWS & EVENT INTELLIGENCE

Berita difungsikan sebagai *context/catalyst*. Sentimen tidak secara langsung mendikte bahwa harga pasti akan naik. `news_loader.py` mencoba mengambil informasi tambahan jika tersedia, mengubah teks menjadi *sentiment score*, yang kemudian dirata-rata ke dalam *Sentiment_MA* dan disertakan ke dalam *feature array* model AI (sebagai pelengkap indikator teknikal murni).

---

## 17. EXPLAINABILITY

Jawaban dari sistem sangat objektif dan berdasarkan perhitungan data konkret.

- **WHY THIS STOCK?** Karena masuk dalam filter *Scanner* di mana Volume Ratio > 1.0 dan MACD menyeberang *Signal Line*.
- **WHY THIS SIGNAL?** Karena *Technical Score* menunjukkan nilai 4/5 ditambah probabilitas model AI yang menunjukkan potensi kenaikan sebesar 68%.
- **WHY THIS ENTRY & TARGET?** Karena nilai *Stop Loss* telah diperhitungkan menggunakan jarak volatilitas normal (1.5x ATR) dan *Take Profit* difokuskan pada rasio R:R minimum.
- **WHAT ARE THE RISKS?** Potensi *error* prediksi (terlihat di metrik RMSE), kondisi *drawdown*, atau kejatuhan harga indeks IHSG.

---

## 18. TEKNOLOGI YANG DIGUNAKAN

**Tech Stack:**

- **Frontend / UI**: `Streamlit` (Python murni). Antarmuka bersih (*sleek dark UI*) dengan *sidebar navigation*.
- **Data Source**: `yfinance` (Data Pasar, OHLCV, Intraday).
- **Backend & Logic**: `Python`
- **Machine Learning**: `scikit-learn` (Random Forest Classifier & Regressor).
- **Model Storage**: Joblib (`.joblib` caching) dan format metadata `.json` untuk penyimpanan lokal di folder `models/`.
- **Data Processing**: `pandas`, `numpy`.

*(Tidak menggunakan platform cloud eksternal atau database SQL, semuanya berjalan locally menggunakan memory & file-based storage).*

---

## 19. ALUR DATA REAL-TIME

Karena batasan penggunaan sumber gratis (`yfinance`), alur data adalah sebagai berikut:

```text
Market Data Provider (yfinance API)
        ↓
Data Ingestion (Download OHLCV saat User mengakses/me-refresh halaman)
        ↓
Data Processing (Drop NaN, Cleaning)
        ↓
Feature Calculation (Add Indicators & ATR)
        ↓
AI Inference (Predict using .joblib loaded models)
        ↓
Dashboard Visualization
```

**Status**: `DELAYED / LAST AVAILABLE`
Sistem akan selalu mengambil titik data harga penutupan terakhir yang tercatat di provider, bukan *real-time websocket streaming*.

---

## 20. DATABASE / MODEL MEMORY

Model dan metadata disimpan dalam folder `models/` sebagai *file-based memory*:

- `[TICKER]_model_[HORIZON]d.joblib`: Memori objek classifier & regressor.
- `[TICKER]_model_[HORIZON]d.meta.json`: Menyimpan skor akurasi (RMSE, F1, ROC-AUC) dan fitur kolom.
- `prediction_history.json`: Menyimpan log prediksi masa lalu (harga saat diprediksi vs hasil pergerakan model). Memungkinkan sistem menjawab *"Bagaimana performa AI selama ini?"* dengan data tersimpan, bukan sekadar prediksi sesaat.

---

## 21. UI / USER EXPERIENCE

Alur UX dirancang menggunakan struktur navigasi yang jelas:

```text
LIVE MARKET CENTER
        ↓
DAFTAR SEMUA SAHAM
        ↓
PETA SEKTOR
        ↓
PEMINDAI JANGKA PENDEK (Screening)
        ↓
ANALISIS SAHAM MENDALAM (Detail Charting)
        ↓
MODE PRESENTASI (Exporting Results)
```

Desain antarmuka fokus pada **professional financial analytics terminal** (*Sleek Dark Mode, solid colors, clean KPI cards*) dengan warna dominan gelap dipadu dengan hijau (`#2ea043`) / merah (`#f85149`) khusus untuk indikasi arah tren harga.

---

## 22. OUTPUT AKHIR UNTUK PRESENTASI

Narasi Presentasi (berdasarkan *Presentation Mode*):

- **Slide 1 — Latar Belakang**: Kompleksitas pergerakan bursa membuat manusia kesulitan menyatukan *Technical, News, dan Risk* sekaligus secara cepat.
- **Slide 2 — Tujuan**: Sistem StockPredict hadir untuk memberi estimasi pergerakan objektif berbasis statistik ML dan skoring indikator teknikal.
- **Slide 3 — Dasar Teori Trading**: Penggunaan Momentum (RSI), Trend (MA), dan Volatilitas (ATR).
- **Slide 4 — Analisis Saham**: Menampilkan metrik *ticker* terpilih.
- **Slide 5 — Analisis Transaksional**: Penyajian skenario letak titik Entry, SL, dan R:R.
- **Slide 6 — Teknikal Trading**: Membedah pembacaan indikator *close-up* pada saham tersebut.
- **Slide 7 — Prediksi Hasil Transaksi**: Menyajikan proyeksi *multi-horizon* (UP/DOWN dengan probabilitas) dari Random Forest yang di-backtest secara kronologis.
- **Slide 8 — Target Transaksi**: Eksekusi akhir target nilai Rupiah (TP1 & TP2).
- **Slide 9 — Kesimpulan**: Hasil konfirmasi ganda (AI + Technical Score = *Final Decision*).

---

## 23. FINAL SYSTEM SUMMARY

```text
PROJECT
↓
AI-Powered Stock Trading Intelligence System (StockPredict)

INPUT
↓
Market Data (OHLCV via yfinance, Historis & Intraday)
Sector Data (TICKER_INFO mapping)
Macro (Indices & Commodities)

PROCESS
↓
Technical Analysis (Indicators Generation)
Feature Engineering (Shifting & Concatenation)
AI/ML Prediction (RandomForest Classifier & Regressor)
Risk Analysis (ATR for SL/TP Sizing)

OUTPUT
↓
Stock Screening (Scanner results)
Future Forecast (Direction, Probability, Predicted Price Bound)
Trading Setup (Entry, TP, SL, R:R)
Historical Prediction Accuracy

INTERFACE
↓
Live Market Center
All Stocks
Sector Map
Short-Term Scanner
Deep Stock Analysis
Presentation Mode (Streamlit-based Professional UI)
```

Tujuan dokumentasi final ini adalah menjembatani celah antara kode murni pemrograman dan rasionalisasi finansial (trading plan) secara end-to-end, memastikan sistem dipahami bukan sebagai "peramal jitu", tetapi sebagai **mesin asisten analisa statistik yang sangat efisien**.

---

## 24. PANDUAN PRESENTASI (KHUSUS UNTUK BACKGROUND IT)

Jika Anda memiliki *background* IT dan merasa tidak percaya diri (insecure) saat mempresentasikan istilah finansial/trading, **jangan berpura-pura menjadi pakar ekonomi/trader pro**. Sebaliknya, **gunakan kekuatan Anda di bidang IT dan Data Science**.

Ubah *framing* presentasinya dari *"Saya mau ngajarin cara trading"* menjadi *"Saya membangun sistem pemrosesan data (pipeline) untuk menyelesaikan masalah analisis data di dunia trading"*.

Berikut adalah *cheat-sheet* skrip presentasi Anda besok untuk 9 poin tersebut:

### 1. Latar Belakang (Framing: Data Overload Problem)

**Skrip:** "Sebagai orang IT, saya melihat masalah utama trader saat ini adalah *Data Overload*. Di bursa saham, ada ratusan saham yang bergerak setiap detik, ditambah rilis berita dan indikator teknikal. Manusia sangat lambat memproses ini secara manual. Oleh karena itu, saya membangun *AI-Powered Trading Support System* untuk mengotomatisasi pemrosesan data, dari harga mentah hingga menjadi *insight* siap pakai."

### 2. Tujuan (Framing: Decision Support System)

**Skrip:** "Tujuan utama sistem ini *bukan* menciptakan robot ajaib pencetak uang pasti untung, karena itu mustahil. Tujuan sistem ini adalah membangun **Decision Support System (Sistem Pendukung Keputusan)** berbasis data. Sistem ini menghitung probabilitas secara objektif agar trader tidak trading hanya mengandalkan *feeling/fomo*."

### 3. Dasar Teori Trading (Framing: Feature Engineering)

**Skrip:** "Dalam dunia trading ada indikator seperti MA (Moving Average), RSI, dan ATR. Dalam kacamata IT/Data Science, semua indikator ini pada dasarnya adalah hasil transformasi matematika (Feature Engineering) dari deret waktu (Time-Series) *Open-High-Low-Close*. Fitur-fitur inilah yang kita berikan sebagai makanan untuk model Machine Learning."

### 4. Analisis Saham (Framing: Data Filtering & Pipeline)

**Skrip:** "Proses analisis saham di sistem saya tidak dilakukan satu persatu secara manual. Sistem melakukan proses *Query* dan *Filtering* secara otomatis. Dari ratusan saham (Universe), difilter berdasarkan sektor, likuiditas, dan tren, sehingga hanya menyisakan saham yang memiliki anomali atau momentum tinggi."

### 5. Analisis Transaksional (Framing: Algorithmic Logic & Risk Optimization)

**Skrip:** "Analisis transaksional di sini pada dasarnya adalah logika optimasi (*Risk/Reward Optimization*). Sistem menghitung jarak dari harga saat ini ke potensi *Take Profit* dan potensi *Stop Loss*. Jika rasio untung dibanding ruginya tidak ideal (misal rasio < 1.5), sistem secara otomatis akan menyarankan untuk tidak masuk posisi (*No Trade*)."

### 6. Teknikal Trading (Framing: Data Visualization & Thresholding)

**Skrip:** "Pada bagian teknikal, sistem ini menyajikan Visualisasi Data yang sudah diperkaya (*enriched data*). Selain itu, kita menggunakan algoritma *scoring* sederhana (Technical Score 0-5). Jika indikator melewati suatu *threshold* tertentu, nilainya naik, sehingga *output* akhirnya sangat kuantitatif."

### 7. Prediksi Hasil (Framing: Machine Learning & Evaluation Metrics)

**Skrip:** "Inilah inti dari kecerdasan sistem (AI-nya). Sistem tidak sekadar menebak, tapi menggunakan algoritma **Random Forest Classifier & Regressor**. Data latihnya di-*split* secara kronologis (tanpa *look-ahead bias*). Sistem mengeluarkan output 'Naik' atau 'Turun' beserta probabilitasnya (Confidence Score). Evaluasinya pun jelas, kita bisa ukur RMSE atau Akurasinya dari data *backtest* masa lalu."

### 8. Target Transaksi (Framing: Dynamic Thresholds / Volatility-based)

**Skrip:** "Untuk menentukan angka pasti kapan harus untung atau rugi, sistem tidak memakai angka tebakan. Sistem menggunakan **ATR (Average True Range)**, yang secara statistik mengukur jarak simpangan harga (volatilitas) harian. Angka ini dijadikan *dynamic threshold* untuk *Stop Loss* dan *Take Profit*."

### 9. Kesimpulan & Rekomendasi (Framing: Dual-Confirmation Output)

**Skrip:** "Kesimpulan akhirnya berasal dari sistem *Dual-Confirmation*. Logic rule-based (Skor Teknikal) digabung dengan probabilitas Machine Learning (AI Forecast). Jika keduanya mengonfirmasi (*True & True*), maka sistem mengeluarkan rekomendasi eksekusi. Dengan sistem ini, pengambil keputusan finansial bisa bekerja murni berdasarkan logika dan statistik."

**Tips Tambahan Besok:**

- Sangat aman bagi Anda mengatakan: *"Secara ekonomi makronya saya mungkin bukan pakarnya, tapi secara arsitektur sistem dan model statistik AI-nya, data menunjukkan bahwa pergerakan ini memiliki probabilitas naik sebesar X%"*. Juri akan sangat mengapresiasi pendekatan teknikal dan analitis Anda yang solid!
