"""
scanner_ui.py — Professional Short-Term / Scalping Scanner UI ⚡

Financial analytics terminal for identifying short-term trading setups.
Designed for actionable analysis, not just indicator display.
"""

import streamlit as st
import pandas as pd
import math
from datetime import datetime

from src.short_term_scanner import (
    fast_scan_universe,
    run_deep_analysis,
    generate_why_this_stock,
    generate_watch_checklist,
    get_scanner_explanation,
    METRIC_TOOLTIPS,
)
from src.ui.market_overview import render_mini_analysis
from src.visualization import COLORS
from src.ui.timing_ui import render_timing_summary, render_full_timing_analysis


# ═══════════════════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════════════════
def render_scanner_ui():
    st.title(":material/radar: Pemindai Jangka Pendek")
    st.caption("Sistem pencari peluang pergerakan saham jangka pendek. Bukan rekomendasi pasti, gunakan dengan bijak.")

    # ── Header / Control Panel ────────────────────────────────────
    col_mode, col_tf, col_n, col_btn = st.columns([1, 1, 1, 1])

    with col_mode:
        mode_opts = {
            "scalping": "Sangat Cepat (Scalping)",
            "intraday": "Harian (Intraday)",
            "1d": "1 Hari",
            "3d": "2-3 Hari",
            "5d": "5 Hari (Standar)",
        }
        mode = st.selectbox("Gaya Trading", list(mode_opts.keys()),
                            format_func=lambda x: mode_opts[x], index=4)

    with col_tf:
        if mode == "scalping":
            tf_opts = {"1m": "1 Min", "5m": "5 Min", "15m": "15 Min"}
        elif mode == "intraday":
            tf_opts = {"15m": "15 Min", "30m": "30 Min", "1h": "1 Hour"}
        else:
            tf_opts = {"1d": "Daily", "1h": "1 Hour", "15m": "15 Min"}
        interval = st.selectbox("Timeframe", list(tf_opts.keys()),
                                format_func=lambda x: tf_opts[x])

    with col_n:
        top_n = st.selectbox("Analisis Top", [10, 15, 20, 30], index=1)

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        run_scan = st.button("Jalankan Pemindaian Cerdas", use_container_width=True, type="primary")

    # ── Data Status ───────────────────────────────────────────────
    now_wib = datetime.now()
    market_hour = 9 <= now_wib.hour <= 16 and now_wib.weekday() < 5
    data_status = "DELAYED (15-20 min)" if market_hour else "LAST AVAILABLE"
    market_status = "OPEN" if market_hour else "CLOSED"

    st.markdown(
        f"**Market:** {market_status} · **Data:** {data_status} · "
        f"**Last Update:** {now_wib.strftime('%Y-%m-%d %H:%M:%S')} WIB · "
        f"**Timeframe:** {tf_opts[interval]}"
    )
    st.markdown("---")

    # ── Run Pipeline ──────────────────────────────────────────────
    if run_scan:
        with st.status("Memindai pasar Indonesia...", expanded=True) as status:
            st.write("Phase 1: Fast screening seluruh saham...")
            fast_results = fast_scan_universe(interval)

            if not fast_results:
                status.update(label="Gagal mengambil data pasar.", state="error")
                return

            st.write(f"✓ {len(fast_results)} saham lolos filter tradeability")
            st.write(f"Phase 2: Deep analysis Top {top_n} (ML + News + Technicals)...")
            deep_results = run_deep_analysis(fast_results, top_n, interval, mode)
            status.update(label=f"Selesai! {len(deep_results)} kandidat dianalisis.", state="complete")

        st.session_state["scanner_results"] = deep_results
        st.session_state["scanner_interval"] = interval
        st.session_state["scanner_mode"] = mode

    results = st.session_state.get("scanner_results", [])
    if not results:
        st.info("Klik **Jalankan Pemindaian Cerdas** untuk memulai pencarian saham.")
        return

    interval = st.session_state.get("scanner_interval", "1d")
    mode = st.session_state.get("scanner_mode", "5d")

    # ══════════════════════════════════════════════════════════════
    # MARKET PULSE
    # ══════════════════════════════════════════════════════════════
    _render_market_pulse(results)

    # ══════════════════════════════════════════════════════════════
    # SCANNER TABLE
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    _render_scanner_table(results)

    # ══════════════════════════════════════════════════════════════
    # QUICK FILTERS + TOP OPPORTUNITIES
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    _render_top_opportunities(results)

    # ══════════════════════════════════════════════════════════════
    # STOCK DETAIL CARDS
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    _render_stock_details(results, interval)

    # ══════════════════════════════════════════════════════════════
    # COMPETITION MODE
    # ══════════════════════════════════════════════════════════════
    st.markdown("---")
    _render_competition_mode(results)


# ═══════════════════════════════════════════════════════════════════
# SECTION RENDERERS
# ═══════════════════════════════════════════════════════════════════

def _render_market_pulse(results):
    """Market-wide summary KPIs."""
    st.markdown("### :material/monitor_heart: Detak Pasar")

    df = pd.DataFrame(results)
    advancing = len(df[df["Change_Pct"] > 0])
    declining = len(df[df["Change_Pct"] < 0])
    unchanged = len(df[df["Change_Pct"] == 0])
    momentum_count = len(df[df["Momentum"].apply(lambda m: m["strength"] == "STRONG")])
    vol_spikes = len(df[df["Volume_Analysis"].apply(lambda v: v["spike"])])
    breakouts = len(df[df["Price_Action"].apply(lambda p: "BREAKOUT" in p.get("patterns", []))])
    high_risk = len(df[df["High_Risk"] == True])

    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
    c1.metric("Total", len(df))
    c2.metric("Advancing", advancing)
    c3.metric("Declining", declining)
    c4.metric("Unchanged", unchanged)
    c5.metric("Momentum", momentum_count)
    c6.metric("Vol Spikes", vol_spikes)
    c7.metric("Breakouts", breakouts)
    c8.metric("High Risk", high_risk, delta_color="inverse")


def _render_scanner_table(results):
    """Main sortable data table."""
    st.markdown("### :material/list_alt: Hasil Pemindaian")

    rows = []
    for i, c in enumerate(results):
        rr = c["Risk_Reward"]
        entry = c["Entry"]
        rows.append({
            "Rank": i + 1,
            "Ticker": c["Ticker"].replace(".JK", ""),
            "Company": c["Company"],
            "Sector": c["Sector"],
            "Score": c["Score"],
            "Price": c["Price"],
            "Perubahan": c["Change_Pct"],
            "Lonjakan Vol.": c["RVOL"],
            "Nilai": c["Trading_Value"],
            "Kekuatan Tren": c["Momentum"]["strength"],
            "Arah Tren": c["Momentum"]["trend"],
            "Sinyal": c["Signal"]["signal"],
            "Area Beli": f"{entry['preferred_low']:,.0f}-{entry['preferred_high']:,.0f}",
            "Target Jual": f"{c['Take_Profit']['tp1']:,.0f}",
            "Batas Rugi": f"{c['Stop_Loss']['price']:,.0f}",
            "Rasio R/R": rr["display"],
            "Berita": c["News"]["impact"],
            "Prediksi AI": c["ML"]["prediction"],
        })

    table_df = pd.DataFrame(rows)
    st.dataframe(
        table_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Score": st.column_config.ProgressColumn("Skor", min_value=0, max_value=100, format="%d"),
            "Price": st.column_config.NumberColumn("Harga", format="Rp %.0f"),
            "Perubahan": st.column_config.NumberColumn("Perubahan 1H", format="%.2f%%"),
            "Lonjakan Vol.": st.column_config.NumberColumn("Lonjakan Vol.", format="%.1fx"),
            "Nilai": st.column_config.NumberColumn("Nilai Transaksi", format="Rp %.0f"),
        },
    )


def _render_top_opportunities(results):
    """Tabs for different opportunity categories."""
    st.markdown("### :material/star: Peluang Terbaik")

    tabs = st.tabs([
        "Kekuatan Tren", "Paling Likuid", "Nilai Tertinggi",
        "Tembus Atas (Breakout)", "Pantulan (Pullback)", "Sangat Cepat",
        "Katalis Berita", "Risiko Rendah", "Risiko Tinggi",
    ])

    def _show_list(items, max_n=5):
        for c in items[:max_n]:
            rr = c["Risk_Reward"]
            signal = c["Signal"]["signal"]
            st.markdown(
                f"**{c['Ticker'].replace('.JK','')}** — Rp {c['Price']:,.0f} "
                f"({'+' if c['Change_Pct']>0 else ''}{c['Change_Pct']:.2f}%) · "
                f"Skor: {c['Score']:.0f} · Lonjakan Vol: {c['RVOL']:.1f}x · "
                f"Rasio R/R: {rr['display']} · Sinyal: {signal}"
            )
            st.caption(get_scanner_explanation(c)[:120])
            st.markdown("---")

    with tabs[0]:  # Momentum
        _show_list(sorted(results, key=lambda x: x["Momentum"]["score"], reverse=True))
    with tabs[1]:  # Liquid
        _show_list(sorted(results, key=lambda x: x["Tradeability"], reverse=True))
    with tabs[2]:  # Value
        _show_list(sorted(results, key=lambda x: x["Trading_Value"], reverse=True))
    with tabs[3]:  # Breakout
        breakouts = [r for r in results if "BREAKOUT" in r["Price_Action"].get("patterns", [])]
        if breakouts:
            _show_list(breakouts)
        else:
            st.info("Tidak ada breakout terdeteksi pada scan terakhir.")
    with tabs[4]:  # Pullback
        pullbacks = [r for r in results if "PULLBACK" in r["Price_Action"].get("patterns", [])]
        if pullbacks:
            _show_list(pullbacks)
        else:
            st.info("Tidak ada pullback terdeteksi pada scan terakhir.")
    with tabs[5]:  # Scalping
        scalps = [r for r in results if r["Scalping"].get("available") and r["Scalping"]["setups"]]
        if scalps:
            for c in scalps[:5]:
                for setup in c["Scalping"]["setups"]:
                    st.markdown(
                        f"**{c['Ticker'].replace('.JK','')}** — {setup['label']} · "
                        f"Area Beli: Rp {setup['entry']:,.0f} · "
                        f"Batas Rugi (SL): Rp {setup['sl']:,.0f} · Target Jual (TP1): Rp {setup['tp1']:,.0f}"
                    )
                    st.caption(f"Syarat Sah: {setup['confirmation']} | Batal Jika: {setup['invalidation']}")
                    st.markdown("---")
        else:
            st.info("Gunakan timeframe intraday (1m/5m/15m) untuk melihat scalping setup.")
    with tabs[6]:  # News
        news_sorted = sorted(results, key=lambda x: x["News"]["score"], reverse=True)
        news_filtered = [r for r in news_sorted if r["News"]["score"] > 2]
        if news_filtered:
            _show_list(news_filtered)
        else:
            st.info("Tidak ada katalis berita signifikan terdeteksi.")
    with tabs[7]:  # Lower Risk
        low_risk = [r for r in results if not r["High_Risk"] and r["Risk_Reward"]["ratio"] >= 1.5]
        low_risk.sort(key=lambda x: x["Risk_Reward"]["ratio"], reverse=True)
        if low_risk:
            _show_list(low_risk)
        else:
            st.info("Tidak ada setup low-risk yang memenuhi kriteria.")
    with tabs[8]:  # High Risk
        risky = [r for r in results if r["High_Risk"]]
        if risky:
            for c in risky:
                st.markdown(f"**:material/warning: {c['Ticker'].replace('.JK','')}** — Rp {c['Price']:,.0f}")
                for reason in c["Risk_Reasons"]:
                    st.error(reason)
                st.markdown("---")
        else:
            st.success("Tidak ada saham dengan risiko tinggi pada scan terakhir.")


def _render_stock_details(results, interval):
    """Expandable detail cards per stock with chart + deep dive."""
    st.markdown("### :material/manage_search: Rincian Saham & Rencana Transaksi")

    page_size = 5
    total_pages = max(1, math.ceil(len(results) / page_size))
    page = st.number_input(
        f"Halaman (1-{total_pages})", min_value=1, max_value=total_pages, value=1,
        key="scanner_detail_page",
    )

    start = (page - 1) * page_size
    current = results[start : start + page_size]

    for cand in current:
        ticker = cand["Ticker"]
        clean = ticker.replace(".JK", "")
        sig = cand["Signal"]["signal"]
        pct = cand["Change_Pct"]
        prefix = "+" if pct > 0 else ""

        with st.expander(
            f"{':material/check_circle:' if sig == 'LONG_SETUP' else ':material/visibility:' if 'WATCH' in sig else ':material/remove:'} "
            f"#{cand['Score']:.0f} | {clean} — {cand['Company']} ({prefix}{pct:.2f}%) — {sig}",
            expanded=True,
        ):
            # ── Chart ──
            render_mini_analysis(
                ticker, cand["Company"], cand["Price"], pct,
                interval=interval, category="scanner_detail",
            )

            st.markdown("---")

            # ── Trade Setup Panel ──
            _render_trade_setup(cand)

            st.markdown("---")

            # ── Why This Stock? ──
            _render_why_section(cand)

            # ── What Should I Watch? ──
            _render_watch_section(cand)

            if "df" in cand:
                st.markdown("---")
                with st.expander(":material/schedule: Lihat Detail Analisis Waktu Transaksi"):
                    render_full_timing_analysis(cand, cand["df"])


def _render_trade_setup(cand):
    """The most important section: actionable trade plan."""
    st.markdown("#### :material/ads_click: Rencana Transaksi")

    entry = cand["Entry"]
    tp = cand["Take_Profit"]
    sl = cand["Stop_Loss"]
    rr = cand["Risk_Reward"]
    eq = cand["Entry_Score"]
    mom = cand["Momentum"]
    vol = cand["Volume_Analysis"]
    vwap = cand["VWAP"]
    sr = cand["Support_Resistance"]

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("**Area Beli (Entry)**")
        st.write(f"Rp {entry['preferred_low']:,.0f} – Rp {entry['preferred_high']:,.0f}")
        for r in entry["reasons"]:
            st.write(f"✓ {r}")
        if entry["avoid"]:
            st.warning(f":material/warning: {entry['avoid_reason']}")

        st.markdown("**Alternatif Beli (Breakout)**")
        st.write(f"Di atas Rp {entry['alt_entry']:,.0f}")

    with col_b:
        st.markdown("**Target Keuntungan (Potensial)**")
        st.write(f"TP1: Rp {tp['tp1']:,.0f} (+{tp['tp1_pct']:.2f}%)")
        st.write(f"TP2: Rp {tp['tp2']:,.0f} (+{tp['tp2_pct']:.2f}%)")
        st.caption("Target potensial, bukan jaminan harga pasti tercapai.")

        st.markdown("**Batas Kerugian (Stop Loss)**")
        st.write(f"SL: Rp {sl['price']:,.0f} (-{sl['loss_pct']:.2f}%)")
        st.caption(f"Metode: {sl['method']}")

    with col_c:
        st.markdown("**Perbandingan Risiko vs Untung**")
        st.metric("Rasio R/R", rr["display"])
        st.write(f"Potensi Untung: +{rr['profit_pct']:.2f}%")
        st.write(f"Potensi Rugi: -{rr['loss_pct']:.2f}%")

        st.markdown("**Kualitas Peluang Beli**")
        st.progress(eq["score"] / 100, text=f"{eq['score']:.0f} / 100")

    # ── Historical Timing Summary ──
    st.markdown("---")
    render_timing_summary(cand)

    # ── Historical Backtest ──
    st.markdown("---")
    st.markdown("**🔬 Uji Balik Historis (Backtest)**")
    st.caption("Simulasi hasil jika strategi ini dijalankan pada 6 bulan terakhir dengan kondisi serupa.")
    bt = cand.get("Backtest", {})
    if bt and bt.get("num_trades", 0) > 0:
        bt1, bt2, bt3, bt4 = st.columns(4)
        bt1.metric("Win Rate", f"{bt.get('win_rate', 0)}%")
        bt2.metric("Total Return", f"{bt.get('total_return', 0)}%")
        bt3.metric("Max Drawdown", f"{bt.get('max_drawdown', 0)}%")
        bt4.metric("Total Trades", bt.get("num_trades", 0))
    else:
        st.info("Data historis tidak mencukupi atau belum ada trigger transaksi dalam 6 bulan terakhir.")

    # ── Technical Snapshot ──
    st.markdown("---")
    st.markdown("**Ringkasan Analisis Teknikal**")
    t1, t2, t3, t4, t5, t6 = st.columns(6)
    t1.metric("Kekuatan Tren", mom["strength"])
    t2.metric("Arah Tren", mom["trend"])
    t3.metric("RSI (Kejenuhan)", f"{mom['rsi']:.0f}")
    t4.metric("Lonjakan Vol.", f"{vol['rvol']:.1f}x")
    t5.metric("Batas Bawah", f"Rp {sr['support']:,.0f}")
    t6.metric("Batas Atas", f"Rp {sr['resistance']:,.0f}")

    if vwap.get("available"):
        v1, v2, v3 = st.columns(3)
        v1.metric("Harga Rata-rata (VWAP)", f"Rp {vwap['vwap']:,.0f}")
        v2.metric("Posisi Harga", vwap["position"])
        v3.metric("Jarak ke VWAP", f"{vwap['distance_pct']:+.2f}%")

    # ── Scalping Setups ──
    scalp = cand["Scalping"]
    if scalp.get("available") and scalp["setups"]:
        st.markdown("---")
        st.markdown("**Peluang Sangat Cepat (Scalping)**")
        for setup in scalp["setups"]:
            st.info(
                f"**{setup['label']}** · Area Beli: Rp {setup['entry']:,.0f} · "
                f"Batas Rugi: Rp {setup['sl']:,.0f} · Target: Rp {setup['tp1']:,.0f}\n\n"
                f"Syarat Sah: {setup['confirmation']}\n\n"
                f"Batal Jika: {setup['invalidation']}"
            )

    # ── Volume Detail ──
    st.markdown("---")
    st.markdown("**Analisis Volume Perdagangan**")
    vc1, vc2, vc3, vc4 = st.columns(4)
    vc1.metric("Volume Saat Ini", f"{vol['current']/1e6:.1f} Jt")
    vc2.metric("Rata-rata Volume", f"{vol['average']/1e6:.1f} Jt")
    vc3.metric("Lonjakan", f"{vol['rvol']:.2f}x")
    vc4.metric("Nilai Transaksi", f"Rp {vol['trading_value']/1e9:.1f} Miliar" if vol['trading_value'] > 1e9 else f"Rp {vol['trading_value']/1e6:.0f} Juta")
    if vol["spike"]:
        st.warning(f":material/local_fire_department: ADA LONJAKAN VOLUME — {vol['spike_level']}")
    st.caption(vol["explanation"])


def _render_why_section(cand):
    """Why this stock? section."""
    why = generate_why_this_stock(cand)
    st.markdown("#### :material/lightbulb: Kenapa Saham Ini Terpilih?")

    col_r, col_c = st.columns(2)
    with col_r:
        for r in why["reasons"]:
            st.write(f"✓ {r}")
    with col_c:
        if why["concerns"]:
            for c in why["concerns"]:
                st.write(f"⚠ {c}")
        else:
            st.write("Tidak ada kekhawatiran signifikan.")


def _render_watch_section(cand):
    """What should I watch? section."""
    watch = generate_watch_checklist(cand)
    st.markdown("#### :material/visibility: Apa yang Harus Diperhatikan?")

    col_w, col_i = st.columns(2)
    with col_w:
        st.markdown("**Sinyal Bagus (Tanda Beli)**")
        for w in watch["confirmations"]:
            st.write(f"✓ {w}")
    with col_i:
        st.markdown("**Sinyal Bahaya (Tanda Jual/Batal)**")
        for inv in watch["invalidations"]:
            st.write(f"✗ {inv}")


def _render_competition_mode(results):
    """1-Week Competition Mode placeholder with session state."""
    st.markdown("### :material/sports_esports: Mode Simulasi Kompetisi")
    st.caption("Latihan trading virtual — tanpa menggunakan uang sungguhan.")

    if "comp_capital" not in st.session_state:
        st.session_state["comp_capital"] = 10_000_000
        st.session_state["comp_positions"] = []
        st.session_state["comp_realized"] = 0

    capital = st.session_state["comp_capital"]
    realized = st.session_state["comp_realized"]
    positions = st.session_state["comp_positions"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Modal Awal", f"Rp {capital:,.0f}")
    c2.metric("Sisa Saldo", f"Rp {capital:,.0f}")
    c3.metric("Untung/Rugi", f"Rp {realized:,.0f}")
    c4.metric("Posisi Terbuka", len(positions))

    st.info(
        "Fitur Competition Mode sedang dalam pengembangan. "
        "Saat ini Anda dapat menggunakan data scanner di atas "
        "untuk referensi analisis trading di sekuritas pilihan Anda."
    )
