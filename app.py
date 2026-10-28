import streamlit as st
import yfinance as yf
import pandas as pd
import warnings
import logging
from datetime import datetime

# फालतू की चेतावनियों को छुपाने के लिए
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

# -------------------------------------------------------------------------
# पेज सेटअप
# -------------------------------------------------------------------------
st.set_page_config(page_title="Master Trading Scanner", page_icon="🚀", layout="wide")
st.title("🚀 Master Trading Scanner (All Stocks & Indices)")
st.write("**CAR + 30,50,200 DMA Breakout + 9/33 EMA Intraday + Pivot Support**")
st.markdown("---")

# -------------------------------------------------------------------------
# मुख्य फंक्शन बनाना (Master Scanner Logic)
# -------------------------------------------------------------------------
def master_stock_scanner(ticker_list):
    results = []
    today_date = datetime.now().strftime("%d-%m-%Y")
    
    # प्रोग्रेस बार वेबसाइट के लिए
    progress_text = st.empty()
    progress_bar = st.progress(0)

    for i, ticker in enumerate(ticker_list):
        progress_text.text(f"Scanning {ticker}... ({i+1}/{len(ticker_list)})")
        try:
            # PART A: DAILY DATA
            daily_data = yf.download(ticker, period="2y", interval="1d", progress=False)
            
            if daily_data.empty or len(daily_data) < 200:
                continue

            close_prices = daily_data['Close'].squeeze()
            high_prices = daily_data['High'].squeeze()
            low_prices = daily_data['Low'].squeeze()

            cmp = float(close_prices.iloc[-1])

            # DMAs की गणना
            dma_30 = float(close_prices.rolling(window=30).mean().iloc[-1])
            dma_50 = float(close_prices.rolling(window=50).mean().iloc[-1])
            dma_200 = float(close_prices.rolling(window=200).mean().iloc[-1])
            dist_200_dma = ((cmp - dma_200) / dma_200) * 100

            # CAR की गणना
            last_1y_data = daily_data.tail(252)
            high_date = last_1y_data['High'].squeeze().idxmax()
            car_data = close_prices.loc[high_date:]
            
            if len(car_data) < 10:
                car_status = 'Negative (Days < 10)'
            else:
                car_values = car_data.expanding().mean()
                last_10_car = car_values.tail(10)
                car_status = 'Positive' if last_10_car.is_monotonic_increasing else 'Negative'

            # Swing Condition
            if (cmp > dma_30) and (cmp > dma_50) and (cmp > dma_200) and (car_status == 'Positive'):
                swing_action = '🟢 Breakout'
            else:
                swing_action = '🔴 Avoid'

            # Pivot Points & Support
            prev_high = float(high_prices.iloc[-2])
            prev_low = float(low_prices.iloc[-2])
            prev_close = float(close_prices.iloc[-2])

            PP = (prev_high + prev_low + prev_close) / 3
            S1 = (2 * PP) - prev_high
            S2 = PP - (prev_high - prev_low)
            S3 = prev_low - 2 * (prev_high - PP)

            if S1 <= 0:
                pos_support, sup_name = PP, "PP"
            elif S2 <= 0:
                pos_support, sup_name = S1, "S1"
            elif S3 <= 0:
                pos_support, sup_name = S2, "S2"
            else:
                pos_support, sup_name = S3, "S3"

            # PART B: INTRADAY DATA
            intraday_data = yf.download(ticker, period="5d", interval="15m", progress=False)
            
            if intraday_data.empty:
                intraday_signal = "N/A"
            else:
                intraday_data['EMA_9'] = intraday_data['Close'].ewm(span=9, adjust=False).mean()
                intraday_data['EMA_33'] = intraday_data['Close'].ewm(span=33, adjust=False).mean()
                
                last_ema9 = float(intraday_data['EMA_9'].iloc[-1])
                last_ema33 = float(intraday_data['EMA_33'].iloc[-1])
                
                intraday_signal = "🟢 BUY" if last_ema9 > last_ema33 else "🔴 SELL"

            # COMPILE DATA
            results.append({
                'Date': today_date,
                'Stock/Index': ticker.replace('.NS', '').replace('^', ''),
                'CMP': round(cmp, 2),
                'Swing Breakout': swing_action,
                'Intraday Signal': intraday_signal,
                'Support Ext': f"{round(pos_support, 2)} ({sup_name})",
                'CAR Status': car_status,
                '200 DMA Dist %': round(dist_200_dma, 2),
                '30 DMA': round(dma_30, 2),
                '50 DMA': round(dma_50, 2),
                '200 DMA': round(dma_200, 2)
            })

        except Exception as e:
            pass
        
        # प्रोग्रेस बार अपडेट
        progress_bar.progress((i + 1) / len(ticker_list))

    progress_text.text("✅ Scanning Complete!")
    df_results = pd.DataFrame(results)
    
    if not df_results.empty:
        df_results = df_results.sort_values(by='200 DMA Dist %', ascending=True)

    return df_results

# -------------------------------------------------------------------------
# EXECUTION (प्रमुख इंडेक्स और 210 शेयर)
# -------------------------------------------------------------------------
my_stocks = [
    '^NSEI', '^NSEBANK', '^CNXFIN', '^BSESN', '^CNXIT', '^CNXAUTO', '^CNXMETAL',
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ABCAPITAL.NS', 'ALKEM.NS', 'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS', 'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS', 'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS', 'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS', 'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COCHINSHIP.NS', 'COFORGE.NS', 'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS', 'CROMPTON.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DELHIVERY.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'ETERNAL.NS', 'EICHERMOT.NS', 'EXIDEIND.NS', 'FORCEMOT.NS', 'NYKAA.NS', 'FORTIS.NS', 'GAIL.NS', 'GVT&D.NS', 'GMRAIRPORT.NS', 'GLENMARK.NS', 'GODFRYPHLP.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCAMC.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HAVELLS.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HAL.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'HINDZINC.NS', 'POWERINDIA.NS', 'HYUNDAI.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS', 'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'NAUKRI.NS', 'INFY.NS', 'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS', 'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS', 'KPITTECH.NS', 'KALYANKJIL.NS', 'KAYNES.NS', 'KFINTECH.NS', 'KOTAKBANK.NS', 'LTF.NS', 'LICHSGFIN.NS', 'LTM.NS', 'LT.NS', 'LAURUSLABS.NS', 'LICI.NS', 'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 'MANAPPURAM.NS', 'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS', 'MFSL.NS', 'MAXHEALTH.NS', 'MAZDOCK.NS', 'MOTILALOFS.NS', 'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS', 'NAM-INDIA.NS', 'NUVAMA.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'OFSS.NS', 'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS', 'PNBHOUSING.NS', 'PAGEIND.NS', 'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS', 'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS', 'PRESTIGE.NS', 'PNB.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RADICO.NS', 'RVNL.NS', 'RELIANCE.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS', 'MOTHERSON.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS', 'SUZLON.NS', 'SWIGGY.NS', 'TATACONSUM.NS', 'TVSMOTOR.NS', 'TCS.NS', 'TATAELXSI.NS', 'TMPV.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TECHM.NS', 'FEDERALBNK.NS', 'INDHOTEL.NS', 'PHOENIXLTD.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS', 'UNOMINDA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'VMM.NS', 'IDEA.NS', 'VOLTAS.NS', 'WAAREEENER.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]

# बटन दबाने पर स्कैनर चलेगा
if st.button("🚀 START MASTER SCANNER", type="primary"):
    master_data = master_stock_scanner(my_stocks)
    
    if not master_data.empty:
        # SUPER TRADES
        st.subheader("🚀 --- SUPER TRADES (Double Confirmation) --- 🚀")
        super_trades = master_data[(master_data['Swing Breakout'] == '🟢 Breakout') & 
                                   (master_data['Intraday Signal'] == '🟢 BUY')]
        
        if super_trades.empty:
            st.info("आज किसी भी स्टॉक में Double Confirmation (Swing + Intraday Buy) नहीं मिला है।")
        else:
            st.dataframe(super_trades[['Stock/Index', 'CMP', 'Swing Breakout', 'Intraday Signal', 'Support Ext', '200 DMA Dist %']], use_container_width=True)

        # FULL REPORT
        st.subheader("📊 पूरी मास्टर रिपोर्ट (All Stocks & Indices)")
        st.dataframe(master_data, use_container_width=True)

        # एक्सेल / CSV डाउनलोड बटन
        csv = master_data.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Full Report",
            data=csv,
            file_name="Master_Trading_Report.csv",
            mime="text/csv",
        )
    else:
        st.error("डेटा फेच करने में कोई तकनीकी दिक्कत आई है। कृपया थोड़ी देर बाद दोबारा कोशिश करें।")
