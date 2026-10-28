import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
from datetime import timedelta

# ==========================================
# 1. PAGE SETUP (वेब-ऐप की सेटिंग)
# ==========================================
st.set_page_config(page_title="Master Trading Setup", page_icon="🚀", layout="wide")

st.title("🚀 Super Unique All-in-One Master Scanner")
st.markdown("**(CAR + 30/50/200 DMA + 9/33 EMA + SMC/Fib Targets + Astro Moon Phase)**")
st.markdown("---")

# ==========================================
# 2. ASTROLOGY (MOON PHASE) LOGIC (Pine Script से)
# ==========================================
def get_moon_phase():
    known_new_moon = datetime.datetime(2024, 1, 11)
    days_since = (datetime.datetime.now() - known_new_moon).days
    moon_phase = days_since % 29.530588
    
    if moon_phase <= 1.5 or moon_phase >= 28.0:
        return "🌑 Amavasya (New Moon) - High Volatility / Reversal expected!"
    elif 13.5 <= moon_phase <= 16.0:
        return "🌕 Purnima (Full Moon) - Trend Reversal expected!"
    else:
        return "🌗 Normal Lunar Phase"

# ==========================================
# 3. SIDEBAR (कंट्रोल पैनल)
# ==========================================
st.sidebar.header("⚙️ Scanner Settings")

# 210 स्टॉक्स की लिस्ट (आप इसे पूरा रख सकते हैं)
full_stock_list = [
    '^NSEI', '^NSEBANK', 'HDFCBANK.NS', 'RELIANCE.NS', 'INFY.NS', 'ICICIBANK.NS', 'TCS.NS', 
    'ITC.NS', 'LT.NS', 'AXISBANK.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'BAJFINANCE.NS', 'ASIANPAINT.NS',
    'M&M.NS', 'MARUTI.NS', 'SUNPHARMA.NS', 'HCLTECH.NS', 'TITAN.NS', 'TATASTEEL.NS', 'TATAMOTORS.NS',
    'HAL.NS', 'ADANIPORTS.NS', 'NTPC.NS', 'POWERGRID.NS', 'ULTRACEMCO.NS', 'ZOMATO.NS', 'JIOFIN.NS'
]

selected_stocks = st.sidebar.multiselect(
    "Select Stocks/Indices to Scan:", 
    full_stock_list, 
    default=['^NSEI', '^NSEBANK', 'HDFCBANK.NS', 'RELIANCE.NS', 'SBIN.NS']
)

use_auto_levels = st.sidebar.checkbox("Use Auto SMC/FIB Targets", value=True)

# ==========================================
# 4. MASTER SCANNER FUNCTION
# ==========================================
@st.cache_data(ttl=300) # 5 मिनट तक डेटा सेव रखेगा ताकि ऐप तेज़ चले
def run_master_scanner(tickers):
    results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, ticker in enumerate(tickers):
        status_text.text(f"Scanning {ticker}... ({i+1}/{len(tickers)})")
        try:
            # A. DAILY DATA
            daily_data = yf.download(ticker, period="2y", interval="1d", progress=False)
            if daily_data.empty or len(daily_data) < 200:
                continue

            close_p = daily_data['Close'].squeeze()
            high_p = daily_data['High'].squeeze()
            low_p = daily_data['Low'].squeeze()

            cmp = float(close_p.iloc[-1])

            # DMAs
            dma_30 = float(close_p.rolling(window=30).mean().iloc[-1])
            dma_50 = float(close_p.rolling(window=50).mean().iloc[-1])
            dma_200 = float(close_p.rolling(window=200).mean().iloc[-1])
            
            # CAR
            high_date = daily_data.tail(252)['High'].squeeze().idxmax()
            car_data = close_p.loc[high_date:]
            if len(car_data) >= 10:
                car_status = 'Positive' if car_data.expanding().mean().tail(10).is_monotonic_increasing else 'Negative'
            else:
                car_status = 'N/A'

            swing_action = '🟢 Breakout' if (cmp > dma_30 and cmp > dma_50 and cmp > dma_200 and car_status == 'Positive') else '🔴 Avoid'

            # B. INTRADAY DATA (9/33 EMA)
            intraday_data = yf.download(ticker, period="5d", interval="15m", progress=False)
            if not intraday_data.empty:
                ema_9 = float(intraday_data['Close'].ewm(span=9, adjust=False).mean().iloc[-1])
                ema_33 = float(intraday_data['Close'].ewm(span=33, adjust=False).mean().iloc[-1])
                intra_signal = "🟢 BUY" if ema_9 > ema_33 else "🔴 SELL"
            else:
                intra_signal = "N/A"

            # C. PINE SCRIPT CUSTOM TARGETS (SMC/FIB/ADR)
            prev_h = float(high_p.iloc[-2])
            prev_l = float(low_p.iloc[-2])
            prev_c = float(close_p.iloc[-2])
            
            pivot = (prev_h + prev_l + prev_c) / 3
            day_range = prev_h - prev_l
            
            # ADR (Average Daily Range - 10 days)
            adr = float((high_p - low_p).tail(10).mean())

            if use_auto_levels:
                buy_above = pivot + (day_range * 0.236)
                sell_below = pivot - (day_range * 0.236)
                target_up1 = buy_above + (adr * 0.382)
                target_dn1 = sell_below - (adr * 0.382)
            else:
                buy_above = sell_below = target_up1 = target_dn1 = 0.0

            results.append({
                'Stock': ticker.replace('.NS', '').replace('^', ''),
                'CMP': round(cmp, 2),
                'Swing Breakout': swing_action,
                'Intraday Signal': intra_signal,
                'Auto Buy Above': round(buy_above, 2),
                'Target 1 (UP)': round(target_up1, 2),
                'Auto Sell Below': round(sell_below, 2),
                'Target 1 (DN)': round(target_dn1, 2),
                'CAR Status': car_status,
                '200 DMA': round(dma_200, 2)
            })

        except Exception as e:
            pass
        
        # Update progress bar
        progress_bar.progress((i + 1) / len(tickers))

    status_text.text("✅ Scanning Complete!")
    return pd.DataFrame(results)

# ==========================================
# 5. UI DISPLAY (डैशबोर्ड)
# ==========================================

# Astro Status
st.info(f"🌌 **Astro Market Status:** {get_moon_phase()}")

if st.sidebar.button("🚀 RUN MASTER SCANNER", type="primary"):
    if len(selected_stocks) > 0:
        df_results = run_master_scanner(selected_stocks)
        
        if not df_results.empty:
            st.subheader("🔥 Super Trades (Double Confirmation)")
            # Filter where Swing is Breakout AND Intraday is BUY
            super_trades = df_results[(df_results['Swing Breakout'] == '🟢 Breakout') & 
                                      (df_results['Intraday Signal'] == '🟢 BUY')]
            
            if not super_trades.empty:
                st.dataframe(super_trades.style.highlight_max(axis=0), use_container_width=True)
            else:
                st.warning("No Super Trades found today based on your strict setup.")

            st.subheader("📊 Full Market Dashboard")
            st.dataframe(df_results, use_container_width=True)
            
            # Streamlit में बाय-डिफ़ॉल्ट डाउनलोड बटन आ जाता है, फिर भी हम CSV दे रहे हैं
            csv = df_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Full Report (CSV)",
                data=csv,
                file_name="Master_Setup_Report.csv",
                mime="text/csv",
            )
        else:
            st.error("No data fetched. Please check symbols or try again later.")
    else:
        st.warning("Please select at least one stock to scan.")
else:
    st.write("👈 Click **'RUN MASTER SCANNER'** in the sidebar to start the magic.")
