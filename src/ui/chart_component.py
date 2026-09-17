"""
chart_component.py — TradingView Lightweight Charts Integration

Injects a custom HTML/JS component into Streamlit to render true interactive,
non-blocking real-time financial charts without triggering Streamlit's redraw loop.
"""

import streamlit.components.v1 as components
import json
import pandas as pd

def render_tradingview_chart(
    df: pd.DataFrame, 
    ticker: str,
    prediction_path: list = None,
    lower_bound: list = None,
    upper_bound: list = None,
    current_price: float = None,
    entry_zone: tuple = None,
    tp: float = None,
    sl: float = None,
    height: int = 600
):
    """
    Renders the lightweight chart in Streamlit.
    """
    
    # Prepare candlestick data
    # TV Lightweight charts expects: {time: 'YYYY-MM-DD', open, high, low, close}
    # For intraday it expects unix timestamp
    
    historical_data = []
    for idx, row in df.iterrows():
        # Convert index to unix timestamp in seconds
        timestamp = int(idx.timestamp()) if hasattr(idx, 'timestamp') else int(pd.to_datetime(idx).timestamp())
        historical_data.append({
            "time": timestamp,
            "open": row["Open"],
            "high": row["High"],
            "low": row["Low"],
            "close": row["Close"],
            "value": row["Volume"] # For volume chart
        })
        
    # Prepare future prediction path
    future_data = []
    if prediction_path and len(prediction_path) > 0:
        last_time = historical_data[-1]["time"]
        # Assume 5m interval for the example. In a real app we'd pass interval seconds.
        # But for UI display, we'll just space them out by 300s (5m)
        interval_sec = 300 
        
        # Start the prediction line at the current actual price
        future_data.append({
            "time": last_time,
            "value": current_price if current_price else historical_data[-1]["close"]
        })
        
        for i, price in enumerate(prediction_path):
            future_data.append({
                "time": last_time + interval_sec * (i + 1),
                "value": price,
                "lower": lower_bound[i] if lower_bound else price,
                "upper": upper_bound[i] if upper_bound else price,
            })
            
    # Serialize data
    hist_json = json.dumps(historical_data)
    fut_json = json.dumps(future_data)
    
    # Optional levels
    levels_json = json.dumps({
        "entry_low": entry_zone[0] if entry_zone else None,
        "entry_high": entry_zone[1] if entry_zone else None,
        "tp": tp,
        "sl": sl
    })

    # The HTML/JS Payload
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background-color: #0e1117; color: #fff; font-family: 'Inter', sans-serif; }}
            #chart-container {{ width: 100%; height: {height}px; position: relative; }}
            .legend {{ position: absolute; left: 12px; top: 12px; z-index: 1; font-size: 14px; line-height: 18px; font-weight: 300; color: #d1d4dc; }}
            .legend-title {{ font-size: 18px; font-weight: bold; color: #fff; margin-bottom: 4px; }}
        </style>
    </head>
    <body>
        <div id="chart-container">
            <div class="legend" id="legend">
                <div class="legend-title">{ticker}</div>
                <div id="legend-values"></div>
            </div>
        </div>

        <script>
            const chartOptions = {{
                layout: {{
                    textColor: '#d1d4dc',
                    background: {{ type: 'solid', color: '#0e1117' }},
                }},
                grid: {{
                    vertLines: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                    horzLines: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                }},
                crosshair: {{
                    mode: LightweightCharts.CrosshairMode.Normal,
                }},
                rightPriceScale: {{
                    borderColor: 'rgba(197, 203, 206, 0.4)',
                }},
                timeScale: {{
                    borderColor: 'rgba(197, 203, 206, 0.4)',
                    timeVisible: true,
                    secondsVisible: false,
                }},
            }};

            const chart = LightweightCharts.createChart(document.getElementById('chart-container'), chartOptions);

            // 1. Main Candlestick Series
            const candleSeries = chart.addCandlestickSeries({{
                upColor: '#2ea043',
                downColor: '#f85149',
                borderDownColor: '#f85149',
                borderUpColor: '#2ea043',
                wickDownColor: '#f85149',
                wickUpColor: '#2ea043',
            }});

            const histData = {hist_json};
            candleSeries.setData(histData);
            
            // 2. Volume Series
            const volumeSeries = chart.addHistogramSeries({{
                priceFormat: {{ type: 'volume' }},
                priceScaleId: '', // set as an overlay
                scaleMargins: {{ top: 0.8, bottom: 0 }},
            }});
            
            const volumeData = histData.map(d => ({{
                time: d.time,
                value: d.value,
                color: d.close >= d.open ? 'rgba(46, 160, 67, 0.5)' : 'rgba(248, 81, 73, 0.5)'
            }}));
            volumeSeries.setData(volumeData);

            // 3. AI Prediction Future Line
            const futData = {fut_json};
            if (futData.length > 0) {{
                const predictionSeries = chart.addLineSeries({{
                    color: '#a78bfa',
                    lineWidth: 2,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    title: 'AI Forecast',
                }});
                
                // Map future data to proper format for line series
                const lineData = futData.map(d => ({{ time: d.time, value: d.value }}));
                predictionSeries.setData(lineData);
                
                // Add Confidence Band (Using Area Series)
                const boundData = futData.filter(d => d.lower && d.upper);
                if (boundData.length > 0) {{
                     // We can simulate an area band by using an area series or two line series filled.
                     // lightweight-charts AreaSeries fills to the bottom, so drawing bands is tricky natively.
                     // The simplest approximation is two lines.
                     
                     const upperSeries = chart.addLineSeries({{
                         color: 'rgba(167, 139, 250, 0.3)',
                         lineWidth: 1,
                         title: 'Upper Range',
                     }});
                     upperSeries.setData(boundData.map(d => ({{ time: d.time, value: d.upper }})));
                     
                     const lowerSeries = chart.addLineSeries({{
                         color: 'rgba(167, 139, 250, 0.3)',
                         lineWidth: 1,
                         title: 'Lower Range',
                     }});
                     lowerSeries.setData(boundData.map(d => ({{ time: d.time, value: d.lower }})));
                }}
            }}
            
            // 4. Trading Levels (Price Lines)
            const levels = {levels_json};
            if (levels.entry_low && levels.entry_high) {{
                candleSeries.createPriceLine({{
                    price: levels.entry_low,
                    color: 'rgba(78, 205, 196, 0.8)',
                    lineWidth: 1,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: 'Entry Zone (L)',
                }});
                candleSeries.createPriceLine({{
                    price: levels.entry_high,
                    color: 'rgba(78, 205, 196, 0.8)',
                    lineWidth: 1,
                    lineStyle: LightweightCharts.LineStyle.Dashed,
                    axisLabelVisible: true,
                    title: 'Entry Zone (H)',
                }});
            }}
            if (levels.tp) {{
                candleSeries.createPriceLine({{
                    price: levels.tp,
                    color: '#2ea043',
                    lineWidth: 2,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: 'Take Profit',
                }});
            }}
            if (levels.sl) {{
                candleSeries.createPriceLine({{
                    price: levels.sl,
                    color: '#f85149',
                    lineWidth: 2,
                    lineStyle: LightweightCharts.LineStyle.Solid,
                    axisLabelVisible: true,
                    title: 'Stop Loss',
                }});
            }}

            // Legend Update logic
            const legendValues = document.getElementById('legend-values');
            chart.subscribeCrosshairMove((param) => {{
                if (param.time) {{
                    const data = param.seriesData.get(candleSeries);
                    if (data) {{
                        const o = data.open.toFixed(0);
                        const h = data.high.toFixed(0);
                        const l = data.low.toFixed(0);
                        const c = data.close.toFixed(0);
                        legendValues.innerHTML = `O: <b>${{o}}</b> H: <b>${{h}}</b> L: <b>${{l}}</b> C: <b>${{c}}</b>`;
                    }}
                }} else {{
                    legendValues.innerHTML = '';
                }}
            }});

            // Auto fit
            chart.timeScale().fitContent();

            // Setup Resize Observer
            new ResizeObserver(entries => {{
                if (entries.length === 0 || entries[0].target !== document.getElementById('chart-container')) return;
                const newRect = entries[0].contentRect;
                chart.applyOptions({{ width: newRect.width, height: newRect.height }});
            }}).observe(document.getElementById('chart-container'));

        </script>
    </body>
    </html>
    """
    
    # Render in Streamlit
    components.html(html_content, height=height)
