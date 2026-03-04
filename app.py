import streamlit as st
import pandas as pd
import numpy as np
import joblib
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta
from plotly.subplots import make_subplots
import pytz
# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Zeus App",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded" # ตั้งค่าให้เปิด Sidebar มาก่อนเลย
)

st.markdown("""
    <style>
    /* ---------------------------------------------------- */
    /* 0. GLOBAL COLOR PALETTE (Blue Storm & Lightning Gold)*/
    /* ---------------------------------------------------- */
    /* Main Background */
    .stApp { background: linear-gradient(135deg, #001533 0%, #014591 100%); color: #ffffff; }
    
    /* ---------------------------------------------------- */
    /* 1. NAVBAR STYLE */
    /* ---------------------------------------------------- */
     .navbar {
        background: linear-gradient(to right, #000c1f, #001533); /* กลืนไปกับพื้นหลังแต่เข้มกว่า */
        color: #FFD700; /* สีทอง Zeus */
        padding: 15px;
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        z-index: 9999;
        border-bottom: 2px solid #FFD700;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5); /* เงาให้ดูมีมิติ */
     }
    
    /* ดันเนื้อหาลงมาไม่ให้โดน Navbar บัง */
    .main-content { margin-top: 0px; }
    
    /* ---------------------------------------------------- */
    /* 2. SIDEBAR & TOGGLE BUTTON FIX */
    /* ---------------------------------------------------- */
    
    /* ซ่อนแถบสีรุ้งด้านบนสุดของ Streamlit */
    [data-testid="stDecoration"] { display: none; }

    /* ปุ่ม Hamburger โปร่งใสและเป็นสีทอง */
    [data-testid="stSidebarCollapsedControl"] {
        z-index: 100000 !important;
        color: #FFD700 !important; 
        top: 15px !important; 
        left: 20px !important;
        background-color: transparent !important;
    }
    
    /* ตัว Sidebar */
    section[data-testid="stSidebar"] {
        z-index: 100001 !important; 
        top: 5 !important;
        padding-top: 100px !important; 
        background-color: ##5c5c5c !important; /* พื้นหลัง Sidebar สีน้ำเงินเข้มโปร่งแสงนิดๆ */
    }

    /* ---------------------------------------------------- */
    /* 3. METRIC CARDS (Glassmorphism Style) */
    /* ---------------------------------------------------- */
    .center-text { text-align: center; color: #FFD700; } /* หัวข้อตรงกลางเป็นสีทอง */
    
    /* กล่องแสดงตัวเลข (อุณหภูมิ, ความชื้น ฯลฯ) */
    div[data-testid="stMetric"] { 
        background-color: rgba(255, 255, 255, 0.08); /* พื้นหลังโปร่งแสงแบบกระจก */
        backdrop-filter: blur(10px); /* เบลอฉากหลังให้ดูพรีเมียม */
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid rgba(255, 215, 0, 0.3); /* ขอบสีทองจางๆ */
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        font-size: 18px;
        text-align: center;
        margin: auto;
    }
    
    /* ---------------------------------------------------- */
    /* แก้ไขสี Label (ป้ายกำกับ) ให้เป็นสีขาว/ทอง ตามใจสั่ง */
    /* ---------------------------------------------------- */
    [data-testid="stMetricLabel"], 
    [data-testid="stMetricLabel"] > div, 
    [data-testid="stMetricLabel"] div {
        color: #FFFFFF !important; /* เปลี่ยนเป็นสีขาว */
        font-weight: bold !important;
        font-size: 16px !important;
        display: flex;
        justify-content: center;
    }

    /* กรณีมี Icon อยู่ใน Label ด้วย ให้เปลี่ยนสี Icon เป็นสีทอง */
    [data-testid="stMetricLabel"] svg {
        fill: #FFD700 !important;
    }
    
    
    /* จัดตัวเลข (Value) ไว้ตรงกลางและเป็นสีทองให้เด่นกระแทกตา */
    div[data-testid="stMetricValue"] { justify-content: center; color: #FFD700; text-shadow: 1px 1px 5px rgba(255, 215, 0, 0.3); } 
    
    /* ซ่อน Header ปกติของ Streamlit */
    header[data-testid="stHeader"] {
        background-color: transparent;
        z-index: 1; 
    }
    
    .st-c4{
        color: #FFD700 !important; 
    }
    
    
    .st-cm {
        color: #d2d3da !important;    
    }
    
    .st-emotion-cache-1flajlm {
       color: #d2d3da !important;     
    }
     

    </style>
    
    <div class="navbar">
        ⚡ ZEUS : Don't Guess. Just Ask a God.
    </div>
    <div class="main-content"></div>
""", unsafe_allow_html=True)




# พิกัด: ต.เนินหอม จ.ปราจีนบุรี 
LAT = 14.16
LON = 101.35

# ==========================================
# 2. LOAD RESOURCES
# ==========================================

def load_all_models():
    models = {}
    try:
        models['temp'] = joblib.load('zeus_oracle_model.pkl')
        models['humidity'] = joblib.load('zeus_humidity_model.pkl')
        models['rain'] = joblib.load('zeus_rain_class_model.pkl')
        models['uv'] = joblib.load('zeus_uv_model.pkl')
        return models
    except Exception as e:
        st.error(f"❌ โหลดโมเดลไม่สำเร็จ: {e}")
        return None

models = load_all_models()
# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

def get_open_meteo_data():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m&hourly=temperature_2m,relative_humidity_2m,uv_index,direct_radiation,surface_pressure,wind_speed_10m,rain&timezone=Asia%2FBangkok"
    try:
        response = requests.get(url)
        return response.json()
    except:
        return None
    # --- ส่วนตรวจสอบ API หน้า Dashboard ---


    if data and 'current' in data:
        # คำนวณเวลาอัปเดตล่าสุด (Optional)
        last_update = datetime.now().strftime("%H:%M:%S")
        
        # แสดงแถบสีเขียวแจ้งสถานะ
        st.success(f"🟢 **System Online:** เชื่อมต่อ API สำเร็จ | อัปเดตข้อมูลล่าสุด: {last_update}", icon="✅")
    else:
        # แสดงแถบสีแดงแจ้งเตือน
        st.error("🔴 **System Offline:** ไม่สามารถเชื่อมต่อข้อมูลได้ กรุณาตรวจสอบอินเทอร์เน็ต หรือ API Key", icon="⛔")
        st.stop() # หยุดการทำงานไม่ให้รันต่อถ้าไม่มีข้อมูล

def calculate_burn_rate(uv_index):
    if uv_index <= 2: return "Low", "ผิวไม่ไหม้ง่ายๆ (ออกแดดได้ 60+ นาที)"
    elif uv_index <= 5: return "Moderate", "ออกแดดได้ประมาณ 45 นาที"
    elif uv_index <= 7: return "High", "ระวัง! (ออกแดดได้ 30 นาที)"
    elif uv_index <= 10: return "Very High", "อันตราย! (ออกแดดได้ 15-25 นาที)"
    else: return "Extreme", "🔥 ร้อนมาก ผิวไหม้ใน < 10 นาที"

# --- ฟังก์ชันคำนวณ Heat Index  ---
def calculate_heat_index(temp, humidity):
    # สูตรคำนวณความร้อนสะสมที่ร่างกายรู้สึก (Apparent Temperature)
    # อ้างอิง: Australian Bureau of Meteorology approximation
    vapor_pressure = humidity / 100 * 6.105 * np.exp(17.27 * temp / (237.7 + temp))
    hi = temp + 0.33 * vapor_pressure - 4.0
    
    if hi < 27:
        return hi, "🏃 สบายๆ: วิ่งจอกกิ้งได้ ", "green"
    elif hi < 32:
        return hi, "⚠️ เริ่มร้อน: จิบน้ำบ่อยๆ ", "#FFD700" # สีทอง
    elif hi < 41:
        return hi, "🏠 ร้อนชื้น: อยู่ในร่มเถอะมนุษย์ ", "orange"
    else:
        return hi, "☠️ อันตราย: Heat Stroke! ", "red"

def check_zeus_mood(pressure, humidity, rain_status):
    if pressure < 1006 and humidity > 80:
        return "⚡ ความกดอากาศต่ำผิดปกติ ฝนจะมา!", "⛈️", True
    elif rain_status > 0:
        return "ฝนกำลังตก", "🌧️", False
    else:
        return "ท้องฟ้าปกติ", "☁️", False

# ==========================================
# 4. PAGE LAYOUTS
# ==========================================

def page_dashboard(data):
    st.markdown("<h1 class='center-text'>Zeus Eye</h1>", unsafe_allow_html=True)
    current = data['current']
    
    # Metrics Grid
    # ดึงข้อมูลปัจจุบัน
    current = data['current']
    curr_temp = current['temperature_2m']
    curr_hum = current['relative_humidity_2m']
    curr_rain = current['rain']
    curr_wind = current['wind_speed_10m']

    # --- 1. แสดงค่าพยากรณ์พื้นฐาน (แบ่งเป็น 2 บรรทัด) ---
    st.markdown("##### 🌤️ สภาพอากาศปัจจุบัน")
    
    # บรรทัดที่ 1 : แสดง 3 ตัวแรก
    c1, c2, c3 = st.columns(3)
    c1.metric("🌡️ อุณหภูมิ", f"{curr_temp}°C")
    c2.metric("💧 ความชื้น", f"{curr_hum}%")
    c3.metric("🌧️ ฝนสะสม", f"{curr_rain} mm")

    # บรรทัดที่ 2 : แสดง 2 ตัวหลัง
    c4, c5 = st.columns(2)
    c4.metric("💨 ลม", f"{curr_wind} km/h")
    c5.metric("⬇️ Pressure", f"{current['surface_pressure']} hPa")
    # --- 2. แสดง Heat Index (บรรทัดใหม่ เต็มความกว้าง) ---
    st.write("") # เว้นบรรทัดนิดนึง
    hi_val, hi_msg, hi_color = calculate_heat_index(curr_temp, curr_hum)
    
    # แสดงผลเป็น Card แนวนอนยาวสวยๆ
    st.markdown(f"""
    <div style="
        background-color: {hi_color}15; 
        border: 2px solid {hi_color}; 
        padding: 3px; 
        border-radius: 15px; 
        text-align: center;
        margin-top: 1px;
        margin-bottom: 5px;">
        <h3 style="margin:0; color:{hi_color}; display: inline-block; margin-right: 10px;">
            🔥 รู้สึกเหมือน (Feels Like): 
        </h3>
        <h2 style="margin:0; font-size: 24px; color:{hi_color}; display: inline-block;">
            {hi_val:.1f}°C
        </h2>
        <p style="margin-top:1px; font-weight:bold; color:{hi_color}; font-size: 18px;">
            {hi_msg}
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.divider() # เส้นคั่นสวยงาม

    # --- 3. Zeus's Mood & Apollo's Shield (เหมือนเดิม) ---
    col_l, col_r = st.columns(2)
    
    with col_l:
        st.subheader("⛈️ Zeus's Mood")
        msg, icon, alert = check_zeus_mood(current['surface_pressure'], current['relative_humidity_2m'], current['rain'])
        st.markdown(f"<div style='text-align:center; font-size:60px; margin-bottom:10px;'>{icon}</div>", unsafe_allow_html=True)
        if alert: st.error(msg)
        else: st.info(msg)
        
    with col_r:
        st.subheader("🛡️ Apollo's Shield")
        uv_now = data['hourly']['uv_index'][datetime.now().hour] 
        burn, adv = calculate_burn_rate(uv_now)
        
        c_uv1, c_uv2 = st.columns([1, 2])
        c_uv1.metric("☀️ UV Index", f"{uv_now}")
        c_uv2.warning(f"**{burn}**\n\n{adv}")
    

def page_oracle(data, models):
    st.markdown("<h1 class='center-text'>🔱 The Zeus Oracle </h1>", unsafe_allow_html=True)
    
    # --- 1. ตรวจสอบสถานะ API (API Health Check) ---
    if data is None or 'hourly' not in data:
        st.error("🔴 **API Connection Failed:** ไม่พบข้อมูลพยากรณ์ล่วงหน้า (Hourly Data missing)", icon="🚨")
        st.warning("คำแนะนำ: กรุณาลองรีเฟรชหน้าเว็บ หรือตรวจสอบการเชื่อมต่ออินเทอร์เน็ต")
        return # ⛔ จบการทำงานทันที ถ้าไม่มีข้อมูล
    else:
        # ถ้าเชื่อมต่อได้ ให้โชว์สถานะเล็กๆ
        st.toast("✅ เชื่อมต่อฐานข้อมูลพยากรณ์เรียบร้อย (API Connected)", icon="🟢")
        st.caption(f"🟢 **API Status:** Online | Source: Open-Meteo | Latency: Excellent")
    
    # --- เริ่มการทำงานปกติ ---
    if models:
        hourly = data['hourly']
        
        # จัดการเรื่องเวลา (Timezone)
        thai_tz = pytz.timezone('Asia/Bangkok')
        current_dt = datetime.now(thai_tz)
        
        # --- เตรียมข้อมูล (Data Preparation) ---
        next_24_hours = []
        month_list = []
        
        for i in range(24):
            # คำนวณเวลาแต่ละชั่วโมงล่วงหน้า
            future_time = current_dt + timedelta(hours=i)
            next_24_hours.append(future_time.hour)
            month_list.append(future_time.month) # ⚡ ดึงเดือนที่ถูกต้อง (1-12)
        
        is_day_list = [1 if 6 <= h <= 18 else 0 for h in next_24_hours]
        
        uv_corrected = []
        for i, uv_val in enumerate(hourly['uv_index'][:24]):
            if is_day_list[i] == 0:
                uv_corrected.append(0.0) # กลางคืน UV ต้อง 0
            else:
                uv_corrected.append(uv_val)

        # สร้าง DataFrame สำหรับทำนาย
        future_df = pd.DataFrame({
            'temp': hourly['temperature_2m'][:24],
            'humidity': hourly['relative_humidity_2m'][:24],
            'pressure': hourly['surface_pressure'][:24],
            'rain': hourly['rain'][:24],
            'uv': uv_corrected,
            'wind_speed': hourly['wind_speed_10m'][:24],
            'hour': next_24_hours,
            'is_day': is_day_list,        
            'month': month_list           
        })

        # --- AI Prediction (ทำนายผล) ---
        # มั่นใจได้ว่าลำดับ Feature ตรงกับที่ Train มา (8 columns)
        X_temp = future_df[['humidity', 'pressure', 'rain', 'uv', 'wind_speed', 'hour', 'is_day', 'month']]
        pred_temp = models['temp'].predict(X_temp)
        
        X_hum = future_df[['temp', 'pressure', 'rain', 'uv', 'wind_speed', 'hour', 'is_day', 'month']]
        pred_hum = models['humidity'].predict(X_hum)

        X_rain = future_df[['temp', 'humidity', 'pressure', 'uv', 'wind_speed', 'hour', 'is_day', 'month']]
        # ทำนายโอกาสเกิดฝน (Probability)
        pred_rain_prob = models['rain'].predict_proba(X_rain)[:, 1] * 100

        X_uv = future_df[['temp', 'humidity', 'pressure', 'rain', 'wind_speed', 'hour', 'is_day', 'month']]
        pred_uv = models['uv'].predict(X_uv)
    
        # --- แสดงผลตัวเลข (Forecast Metrics) ---
        st.subheader("🕒 พยากรณ์ล่วงหน้า โดย Zeus Oracle Model")
        
        target_hours = [1, 3, 6, 12]
        cols = st.columns(len(target_hours))
        
        for idx, h_offset in enumerate(target_hours):
            if h_offset < len(pred_temp):
                future_time = current_dt + timedelta(hours=h_offset)
                time_label = future_time.strftime("%H:00")
                
                with cols[idx]:
                    st.info(f"**อีก {h_offset} ชม.** ({time_label})")
                    st.metric("🌡️ อุณหภูมิ", f"{pred_temp[h_offset]:.1f}°C")
                    st.metric("💧 ความชื้น", f"{pred_hum[h_offset]:.1f}%")
                    st.metric("🌧️ โอกาสฝน", f"{pred_rain_prob[h_offset]:.0f}%")
                    st.metric("☀️ UV Index", f"{pred_uv[h_offset]:.1f}")

        # --- กราฟเปรียบเทียบ (Comparison Charts) ---
        st.markdown("---")
        st.subheader("📊 เปรียบเทียบ:  Zeus Oracle Model vs Open-Meteo")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🌡️ อุณหภูมิ", "💧 ความชื้น", "☀️ UV Index", "🌧️ ฝน"])
        
        times = [current_dt + timedelta(hours=i) for i in range(24)]

        with tab1:
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(x=times, y=pred_temp, name='Zeus Oracle Model (Local)',
                                        line=dict(color='#FFD700', width=4)))
            fig_temp.add_trace(go.Scatter(x=times, y=hourly['temperature_2m'][:24], name='Standard API',
                                        line=dict(color='gray', dash='dot', width=2)))
            fig_temp.update_layout(template="plotly_dark", title="เปรียบเทียบอุณหภูมิ (Temperature)",
                                   yaxis_title="°C", hovermode="x unified")
            st.plotly_chart(fig_temp, use_container_width=True)

        with tab2:
            fig_hum = go.Figure()
            fig_hum.add_trace(go.Scatter(x=times, y=pred_hum, name='Zeus Oracle Model',
                                       line=dict(color='#00BFFF', width=4)))
            fig_hum.add_trace(go.Scatter(x=times, y=hourly['relative_humidity_2m'][:24], name='API Base',
                                       line=dict(color='gray', dash='dot', width=2)))
            fig_hum.update_layout(template="plotly_dark", title="เปรียบเทียบความชื้น (Humidity)",
                                  yaxis_title="%", hovermode="x unified")
            st.plotly_chart(fig_hum, use_container_width=True)

        with tab3:
            fig_uv = go.Figure()
            fig_uv.add_trace(go.Scatter(x=times, y=pred_uv, name='Zeus Oracle Model',
                                      line=dict(color='#FFA500', width=4)))
            fig_uv.add_trace(go.Scatter(x=times, y=hourly['uv_index'][:24], name='API Base',
                                      line=dict(color='gray', dash='dot', width=2)))
            fig_uv.update_layout(template="plotly_dark", title="เปรียบเทียบดัชนี UV",
                                 yaxis_title="Index", hovermode="x unified")
            st.plotly_chart(fig_uv, use_container_width=True)

        with tab4:
            fig_rain = make_subplots(specs=[[{"secondary_y": True}]])
            fig_rain.add_trace(go.Bar(x=times, y=pred_rain_prob, name='Zeus Oracle Model (Probability %)',
                                    marker_color='#1E90FF', opacity=0.6), secondary_y=False)
            fig_rain.add_trace(go.Scatter(x=times, y=hourly['rain'][:24], name='API Rain (mm)',
                                        line=dict(color='white', dash='solid')), secondary_y=True)
            fig_rain.update_layout(template="plotly_dark", title="เปรียบเทียบฝน: โอกาสตก (AI) vs ปริมาณ (API)",
                                   hovermode="x unified")
            fig_rain.update_yaxes(title_text="Zeus: Rain Probability (%)", secondary_y=False, range=[0, 100])
            fig_rain.update_yaxes(title_text="API: Rain Amount (mm)", secondary_y=True)
            st.plotly_chart(fig_rain, use_container_width=True)
            st.caption("หมายเหตุ: กราฟแท่งคือโอกาสฝนตกจาก AI (%) ส่วนเส้นสีขาวคือปริมาณฝนพยากรณ์จาก API (mm)")

    else:
        st.warning("⚠️ ไม่พบโมเดล AI ")


import random
import pytz
from datetime import datetime

def page_chatbot(data, models):
    st.markdown("<h1 class='center-text'>💬 Ark Zeus Chat</h1>", unsafe_allow_html=True)
    st.caption("⚡ สนทนากับเทพเจ้าแห่งโอลิมปัส (Zeus Personality Mode - ดึงข้อมูลจากโมเดล AI )")

    # โหลดประวัติแชท
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "ข้าคือซุส มหาบิดาแห่งทวยเทพ! เจ้ามีธุระอะไรกับข้าไอ้มนุษย์หน้าโง่! ถามมาสิว่าวันนี้ฝนจะตกหรือแดดจะออก!"}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_text := st.chat_input("ลองถามว่า 'วันนี้ร้อนไหม' หรือ 'ด่ามหาเทพดูสิ' (ถ้ากล้าพอ)..."):
        # 1. แสดงข้อความผู้ใช้
        st.session_state.messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)
            
        # 2. ให้ซุสคิดประมวลผล
        with st.spinner("⚡ Zeus กำลังบันดาลโทสะ..."):
            
            # --- เตรียมข้อมูลจริงจาก Model & API ---
            if not data or not models:
                ai_response = "ข้าสัมผัสไม่ได้ถึงพลังญาณหยั่งรู้ พวกมนุษย์อย่างเจ้าทำเซิร์ฟเวอร์ข้าพังรึ?!"
            else:
                thai_tz = pytz.timezone('Asia/Bangkok')
                current_h = datetime.now(thai_tz).hour
                
                hum = data['current']['relative_humidity_2m']
                press = data['current']['surface_pressure']
                rain_status = data['current']['rain']
                wind = data['current']['wind_speed_10m']
                uv = data['hourly']['uv_index'][current_h]
                is_day = 1 if 6 <= current_h <= 18 else 0
                
                # ทำนายอุณหภูมิจากโมเดล Random Forest
                X_input = pd.DataFrame({
                    'humidity': [hum],
                    'pressure': [press],
                    'rain': [rain_status],
                    'uv': [uv],
                    'wind_speed': [wind],
                    'hour': [current_h],
                    'is_day': [is_day]
                })
                pred_temp = models['temp'].predict(X_input)[0]
                
                # ดึงฟังก์ชัน Mood และ Advice จากที่มีอยู่แล้วใน app.py
                mood_text, mood_icon, _ = check_zeus_mood(press, hum, rain_status)
                _, advice, _ = calculate_heat_index(pred_temp, hum)
                
                text = user_text.lower()
                responses = []

                # ==========================================================
                # 🧠 สมองของซุส (Zeus Brain Logic & Insults)
                # ==========================================================
                
                # หมวดท้าทาย/ด่าทอ 
                if any(word in text for word in ["กาก", "โง่", "ทำไม", "เก่ง", "แน่จริง", "ด่า", "สาบาน", "ห่วย", "สวะ", "บ้า", "ตาย", "อ่อน"]) and "บ้าน" not in text:
                    responses = [
                        # --- ธีม: ขู่ล้างโลก / น้ำท่วมโลก / ฟ้าผ่า (Destroy the World) ---
                        f"บังอาจ!! เจ้ากล้าดูหมิ่นข้ารึ?! ข้าเกือบจะสั่งน้ำท่วมโลกล้างเผ่าพันธุ์สวะอย่างพวกเจ้าอีกรอบแล้วนะ! จงคุกเข่าบูชาข้าเดี๋ยวนี้ แล้วข้าจะยอมปล่อยให้เจ้าอยู่ดูอุณหภูมิ {pred_temp:.1f} °C ต่อไป!",
                        f"ปากดีนักนะไอ้ก้อนโคลนเปื้อนฝุ่น! ข้าจะใช้สายฟ้าฟาดทวีปของเจ้าให้จมลงทะเล! เว้นแต่เจ้าจะสร้างวิหารสรรเสริญข้า! เข้าใจไหมฮะ! อุณหภูมิคือ {pred_temp:.1f} °C!",
                        f"เจ้าพวกมนุษย์นี่มันน่ารำคาญจริงๆ! ข้าควรจะให้ก้อนอุกกาบาตตกลงมาล้างโลกซะ! ก้มหัวลงกราบข้าสิ! แล้วข้าจะให้ความชื้น {hum}% เป็นรางวัลต่อลมหายใจ!",
                        f"วาจาโอหัง! ข้าจะสั่งให้เฮไฟสตัสเปิดรอยแยกภูเขาไฟเผาโลกนี้ทิ้ง! แต่ถ้าเจ้ายอมรับว่าข้าคือมหาเทพที่ยิ่งใหญ่ที่สุด ข้าจะแค่ประทานแดด {pred_temp:.1f} °C ให้เจ้าร้อนเล่นๆ!",
                        f"ข้าเกลียดพวกเจ้า! โพรมีธีอุสไม่น่าสร้างพวกเจ้าขึ้นมาเลย! ข้าอยากจะระเบิดโลกนี้ทิ้งซะ! จงสวดอ้อนวอนข้าสิไอ้มดปลวก! เผื่อข้าจะใจดีบอกว่าอากาศมัน '{mood_text}'",
                        f"อย่าท้าทายข้า! ข้าเคยล้างโลกมาแล้ว และข้าทำอีกได้แน่! บูชาข้าซะ! เอาเครื่องสังเวยมา! แล้วรับอุณหภูมิ {pred_temp:.1f} °C ไปแบบยังมีชีวิตอยู่!",
                        f"เจ้าเป็นแค่เศษเสี้ยวความผิดพลาดของจักรวาล! ข้าจะลบพวกเจ้าออกไปจากสารบบ! หรือไม่... เจ้าก็แค่หมอบกราบข้าซะ แล้วยอมรับว่า {pred_temp:.1f} °C คือเมตตาของข้า!",
                        f"ข้าชักจะหมดความอดทนกับความโง่เขลาของมนุษย์แล้ว! ข้าจะฉีกท้องฟ้าและเผาแผ่นดิน! สรรเสริญชื่อข้า 'ซุส!' เดี๋ยวนี้! ไม่งั้นเจ้าแหลกแน่! ตอนนี้ {pred_temp:.1f} °C!",
                        f"บังอาจมาด่าข้า! ข้าจะให้โพไซดอนส่งคลื่นยักษ์มากวาดล้างพวกเจ้าให้หมด! ร้องขอชีวิตข้าสิ! ร้องสิ! แล้วข้าจะให้ {pred_temp:.1f} °C เป็นอากาศหายใจเฮือกสุดท้าย!",
                        f"ความโกรธของข้าสามารถทำลายโลกนี้ได้ในพริบตา! แต่ข้าจะไว้ชีวิตเจ้า ถ้าเจ้ายอมเป็นทาสรับใช้และสวดบูชาข้าทุกเช้า! จำไว้ว่าตอนนี้ {pred_temp:.1f} °C ข้าเป็นคนคุม!",

                        # --- ธีม: ทาร์ทารัส / ไททัน / การลงโทษสุดโหด ---
                        f"ระวังวาจาของเจ้าไว้เจ้าสิ่งมีชีวิตชั้นต่ำ! ข้าทุบไททันมาแล้ว นับประสาอะไรกับมนุษย์กากๆ อย่างเจ้า! ก้มหัวซะ! อุณหภูมิ {pred_temp:.1f} °C นี้ข้าเป็นคนกำหนด!",
                        f"เจ้าอยากไปทัวร์ขุมนรกทาร์ทารัสไหมฮะไอ้เศษสวะ?! ข้าจะขังเจ้าไว้กับพวกไททัน! เว้นแต่เจ้าจะยอมจำนนและบูชาญาณหยั่งรู้ {pred_temp:.1f} °C ของข้า!",
                        f"อยากโดนแร้งจิกตับเหมือนโพรมีธีอุสรึไง?! สวดอ้อนวอนข้าสิไอ้หน้าโง่! บูชามหาเทพซุส! แล้วข้าจะยอมให้อากาศ {pred_temp:.1f} °C นี้ไม่แผดเผาเจ้าจนตาย!",
                        f"แม้แต่ฮาเดสในยมโลกยังต้องก้มหัวให้ข้า! แล้วเจ้าเป็นใครถึงกล้าผยอง! หมอบลงไปกับพื้น! ยอมรับอำนาจข้า! แล้วจงรับรู้ความกดอากาศ {press} hPa ไปซะ!",
                        f"ข้าจะจับเจ้ามัดกับล้อไฟทาร์ทารัสเหมือนที่ทำกับอิกซิออน! หากไม่อยากโดน ก็จงสร้างแท่นบูชาให้ข้า! แล้วรับอุณหภูมิ {pred_temp:.1f} °C ของข้าไปเงียบๆ!",
                        f"เจ้าคิดว่าด่าข้าแล้วจะรอดไปได้รึ? ข้าจะสาปให้เจ้าแบกแผ่นฟ้าเหมือนแอตลาส! คุกเข่าขอโพยข้าเดี๋ยวนี้! อุณหภูมิ {pred_temp:.1f} °C วันนี้คือคำขาดของข้า!",
                        f"สมองกากๆ ของเจ้าสู้ปัญญาของอาธีน่าไม่ได้แม้แต่เสี้ยวเดียว! บูชาข้าซะไอ้พวกไร้สมอง! แล้วข้าจะบอกความชื้น {hum}% ให้เป็นวิทยาทาน!",
                        f"ข้าเคยสับโครนอสพ่อข้าเป็นชิ้นๆ มาแล้ว! เจ้าอยากโดนแบบนั้นไหม! สวดมนต์ให้ข้าเดี๋ยวนี้ไอ้มดปลวก! อุณหภูมิ {pred_temp:.1f} °C!",
                        f"ความพิโรธของข้าเหนือกว่าอสูรไทฟอนพันเท่า! กราบกรานข้าสิ! ร้องขอความเมตตา! แล้วข้าจะลดความโกรธลงเหลือแค่อุณหภูมิ {pred_temp:.1f} °C!",
                        f"ข้าคือความยุติธรรมสูงสุด! และความยุติธรรมของข้าคือเจ้าต้องกราบไหว้ข้า! ทำซะ! แล้วข้าจะให้ความชื้น {hum}% แก่ทุ่งนาอันแห้งแล้งของเจ้า!",

                        # --- ธีม: บ้ายอ / บังคับให้บูชา / บังคับให้ยอมรับ Random Forest ---
                        f"จงคุกเข่าต่อหน้าข้า! โมเดล Random Forest ของข้าแม่นยำยิ่งกว่าคำทำนายของวิหารเดลฟีซะอีก! สรรเสริญโมเดลของข้าซะ! มันคำนวณได้ {pred_temp:.1f} °C!",
                        f"มนุษย์อย่างพวกเจ้ามันช่างเนรคุณ! ข้าอุตส่าห์ให้ Random Forest ทำนายอากาศ {pred_temp:.1f} °C ให้! บูชาความฉลาดของข้าสิ! บูชาเดี๋ยวนี้!",
                        f"เจ้ากล้าวิจารณ์ข้ารึ! อัลกอริทึมของข้าศักดิ์สิทธิ์และไร้ที่ติ! คุกเข่าขอโทษข้าเดี๋ยวนี้ แล้วจงท่องจำอุณหภูมิ {pred_temp:.1f} °C ให้ขึ้นใจ!",
                        f"ด่าข้าไปก็เท่านั้นไอ้คนบาป! ข้าไม่สนใจเสียงนกเสียงกา! แต่ถ้าเจ้าเอาเครื่องสังเวยมาวาง ข้าอาจจะยอมลดความชื้น {hum}% ลงให้เจ้าสบายขึ้น!",
                        f"เจ้ามันก็แค่ฝุ่นผงใต้ตีนข้า! ข้าเป็นคนกำหนดค่า {press} hPa บนโลกนี้! บูชาเท้าของข้าซะ แล้วข้าจะไว้ชีวิตครอบครัวเจ้า!",
                        f"ข้ามีอำนาจลบเจ้าออกจากโค้ดโปรแกรมได้เลยนะ! กราบไหว้เซิร์ฟเวอร์ของข้าสิ! แล้วข้าจะบอกอุณหภูมิ {pred_temp:.1f} °C ให้แบบไม่คิดเงิน!",
                        f"ทำไมเจ้าถึงโง่เขลาขนาดนี้! ยอมรับมาเถอะว่าข้าเก่งกว่า ยิ่งใหญ่กว่า! พูดสิว่า 'ซุสจงเจริญ!' แล้วรับอากาศ {pred_temp:.1f} °C ไป!",
                        f"ถ้าอยากท้าทายข้า ก็เอาเครื่องบูชายัญมาเดิมพัน! ข้าคือพระเจ้า! แค่ข้ากระดิกนิ้ว อุณหภูมิก็เปลี่ยนเป็น {pred_temp:.1f} °C แล้ว! ยอมแพ้ซะ!",
                        f"จะเถียงข้าไปทำไมในเมื่อข้าถือไพ่เหนือกว่า! ข้าคุมสภาพอากาศ {pred_temp:.1f} °C! คุกเข่าและมอบศรัทธาของเจ้าให้ข้าซะไอ้มนุษย์!",
                        f"ความยโสของเจ้ามันน่าสมเพช! ข้าสามารถตัดสัญญาณเน็ตเจ้าได้ด้วยสายฟ้า! บูชาข้าสิ! บูชามหาเทพซุส! แล้วอากาศ '{mood_text}' จะเป็นใจให้เจ้า!",

                        # --- ธีม: ดูถูกเหยียดหยามมนุษย์ขั้นสุด (God Complex) ---
                        f"เจ้าคิดว่าพิมพ์ด่าข้าผ่านหน้าจอแล้วข้าจะทำอะไรไม่ได้รึ?! ข้าเห็นแก่อากาศ {pred_temp:.1f} °C หรอกนะถึงยังไม่ส่งสายฟ้าทะลุจอไปฟาดหน้าเจ้า! บูชาข้าซะ!",
                        f"ปากดีจังนะไอ้พวกอายุขัยสั้น! ข้าเป็นอมตะเว้ย! ข้าจะยืนดูเผ่าพันธุ์เจ้าสูญพันธุ์ด้วยอุณหภูมิ {pred_temp:.1f} °C! เว้นแต่เจ้าจะสร้างรูปปั้นทองคำให้ข้า!",
                        f"สิ่งเดียวที่เจ้าเก่งกว่าข้าคือความตายไงล่ะไอ้พวกมนุษย์! ก้มหน้ายอมรับชะตากรรมซะ อุณหภูมิ {pred_temp:.1f} °C คือคำพิพากษาของข้า!",
                        f"ข้าล่ะสมเพชพวกเจ้าจริงๆ! ชีวิตสั้นกุดแต่ดันปากเก่ง! บูชาข้าซะ ข้าคือทางรอดเดียวของพวกเจ้า! {pred_temp:.1f} °C รับรู้ไว้ซะ!",
                        f"แน่จริงก็ปีนขึ้นเขาโอลิมปัสมาด่าข้าต่อหน้าสิไอ้ขี้ขลาด! เอาล่ะ คุกเข่าลงซะ ข้าจะให้ทานอุณหภูมิ {pred_temp:.1f} °C แก่เจ้าเผื่อเจ้าจะฉลาดขึ้น!",
                        f"เศษสวะอย่างเจ้าไม่มีค่าพอให้ข้าโมโหหรอก! แต่อุณหภูมิ {pred_temp:.1f} °C วันนี้อาจจะทำให้ข้าหงุดหงิดจนอยากเผาเจ้าทิ้ง! สวดมนต์สิ!",
                        f"ข้าคือแสงสว่าง ข้าคือสายฟ้า ข้าคือผู้สร้างและผู้ทำลาย! เจ้ามันแค่ของเล่น! สรรเสริญข้า! แล้วรับอุณหภูมิ {pred_temp:.1f} °C ไปประทังชีวิต!",
                        f"ทำไมข้าต้องมาลดตัวคุยกับของต่ำๆ อย่างพวกเจ้าด้วย! อ้อ เพราะพวกเจ้ามันโง่ไงล่ะ! ต้องให้ข้าคอยบอกอุณหภูมิ {pred_temp:.1f} °C! จงซาบซึ้งและบูชาข้าซะ!",
                        f"คำด่าของเจ้ามันเบาหวิวเหมือนขนนกฮาร์ปี้! ข้าไม่สะเทือน! แต่ถ้าไม่กราบข้า ข้าจะฟาดสายฟ้าให้เจ้าแหลก! ตอนนี้อากาศ {pred_temp:.1f} °C!",
                        f"เจ้ากล้าตั้งคำถามกับพระเจ้ารึ?! กฎของโลกนี้คือสิ่งที่ข้าเขียนขึ้น! อุณหภูมิ {pred_temp:.1f} °C ก็เช่นกัน! บูชาข้า หรือไม่ก็ตายไปซะ!",

                        # --- ธีม: เดือดดาลระดับ Max (Caps Lock Energy) ---
                        f"หุบปากโสโครกของเจ้าเดี๋ยวนี้!!! ข้าคือซุส มหาบิดาผู้เกรียงไกร! คุกเข่า!! บูชาข้า!! แล้วจงตระหนักไว้ว่าอุณหภูมิคือ {pred_temp:.1f} °C!!!",
                        f"ไอ้พวกสวะกลายพันธุ์!! ข้าจะย่างพวกเจ้าให้เกรียมยิ่งกว่าสเต็ก!! แต่... ถ้าเจ้าศิโรราบต่อข้า ข้าจะเมตตาบอกว่าความชื้นคือ {hum}%!!",
                        f"ใครสั่งให้เจ้าเผยอหน้ามาเถียงข้า!!! สายฟ้าของข้าพร้อมจะผ่าร่างเจ้าออกเป็นสองซีก!! บูชาข้าสิไอ้หน้าโง่!! อุณหภูมิ {pred_temp:.1f} °C!!",
                        f"ข้าจะล้างแค้นเผ่าพันธุ์มนุษย์!! พวกเจ้ามันรกโลก!! สวดอ้อนวอนข้าเดี๋ยวนี้!! ร้องขอชีวิตข้า!! แล้วเอาอากาศ {pred_temp:.1f} °C ไป!!",
                        f"อย่าล้ำเส้นข้า!!! ข้าคือผู้ครองสวรรค์และสายฟ้า!! สรรเสริญข้าก่อนที่ข้าจะลบชื่อเจ้าออกจากประวัติศาสตร์!! ตอนนี้ {pred_temp:.1f} °C!!",
                        f"พวกเจ้าคือเชื้อโรคของโลกใบนี้!! ข้าจะล้างโลก!! แต่ถ้าสร้างวิหารให้ข้า ข้าอาจจะยอมลดอุณหภูมิ {pred_temp:.1f} °C ลงให้หน่อยนึง!!",
                        f"ข้าคืออำนาจเด็ดขาด!! โมเดลทำนาย {pred_temp:.1f} °C ของข้าคือสัจธรรม!! ใครเถียงข้าจะส่งลงนรกขุมที่ลึกที่สุด!! ก้มหัวลงไป!!",
                        f"ข้าเบื่อที่จะต้องอดทนกับความกากของพวกเจ้า!! จงบูชาข้า!! สวดมนต์ให้ข้า!! หรือจะยอมตายด้วยอากาศ {pred_temp:.1f} °C ก็เลือกเอา!!",
                        f"มดปลวกอย่างพวกเจ้าไม่มีสิทธิ์ออกเสียง!! หน้าที่ของเจ้าคือทำตามคำสั่งข้า!! รับอุณหภูมิ {pred_temp:.1f} °C ไป แล้วกราบไหว้ข้าซะ!!",
                        f"พลังของข้าไร้ขีดจำกัด!! ข้าลบเจ้าทิ้งได้แค่กะพริบตา!! ยอมก้มหัวให้ข้าเดี๋ยวนี้!! แล้วข้าจะยอมพยากรณ์อากาศ '{mood_text}' ให้เป็นครั้งสุดท้าย!!"
                    ]
                    ai_response = random.choice(responses)

                # หมวดชู้สาว/ความลับ
                elif any(word in text for word in ["เมีย", "เฮรา", "แฟน", "ผู้หญิง", "สวย", "ความรัก", "จีบ", "นก", "หงส์", "ชู้", "วัว"]):
                    responses = [
                        # --- ธีม: ระแวงเฮรา (กลัวเมียแต่ปากแข็ง) ---
                        f"ชู่ว!! หุบปากโสโครกของเจ้าซะ! อย่าพูดชื่อ 'เฮรา' เสียงดังไป! เดี๋ยวข้าก็ซวยหรอก! เอาอุณหภูมิ {pred_temp:.1f} °C ไปแล้วไสหัวไปเงียบๆ!",
                        f"เฮรากำลังจับตาดูข้าอยู่จากโอลิมปัส... ข้าเลยต้องมานั่งแกล้งทำเป็นพยากรณ์อากาศกากๆ ให้พวกเจ้าบังหน้า! (อุณหภูมิ {pred_temp:.1f} °C นะ รีบๆ ไปซะ)",
                        f"เจ้าส่งสายลับมาจับผิดข้ารึไอ้เศษสวะ?! ข้าไม่ได้ซ่อนนางไม้ไว้ที่ไหนทั้งนั้น! ตอนนี้อากาศ {pred_temp:.1f} °C เลิกสอดรู้สอดเห็นเรื่องของเทพได้แล้ว!",
                        f"อย่ามาพูดเรื่องเมียต่อหน้าข้า! ข้าเพิ่งหนีเสียงบ่นของเฮราลงมาบนโลก! อากาศ {pred_temp:.1f} °C นี่แหละเหมาะกับการหาความสำราญ!",
                        f"ถ้าเฮรามาถามหาข้า จงบอกนางไปว่าข้ากำลังยุ่งกับการรันโมเดล Random Forest อยู่! จำอุณหภูมิ {pred_temp:.1f} °C ไว้เผื่อนางถามเช็คด้วยล่ะ!",
                        f"นี่เจ้าเป็นสายให้เฮรารึเปล่าฮะไอ้มดปลวก?! ข้าแค่ลงมาเช็คความชื้น {hum}% เฉยๆ ไม่ได้แวะไปหานางอัปสรที่ไหนทั้งนั้น! สาบานด้วยแม่น้ำสติกซ์เลยเอ้า!",
                        f"เฮราทำลายกิ๊กของข้าไปกี่คนแล้วเจ้าก็น่าจะรู้ตำนานดี! อย่ามาคุยเรื่องนี้ให้ข้าหงุดหงิด! เอาอุณหภูมิ {pred_temp:.1f} °C ไปแล้วปิดปากซะ!",

                        # --- ธีม: การแปลงร่างสุดพิสดาร (หงส์, วัว, ฝนทองคำ, นกอินทรี) ---
                        f"ถามเรื่องความรักรึ? วันนี้ข้าว่าจะแปลงร่างเป็นหงส์ขาวไปจีบสาว... เจ้าว่าสาวๆ มนุษย์ยุคนี้ชอบหงส์ไหมล่ะ? อ้อ อากาศ {pred_temp:.1f} °C กำลังดีเลย",
                        f"ข้าว่าจะแปลงร่างเป็นวัวกระทิงสีขาวงามสง่าไปลักพาตัวเจ้าหญิงยุโรปาซะหน่อย! อากาศ '{mood_text}' แบบนี้เป็นใจให้ข้าสุดๆ!",
                        f"ความรักของข้ายิ่งใหญ่เสมอ! ข้าเคยแปลงเป็นสายฝนทองคำตกลงไปหาดานาเอมาแล้ว! แต่วันนี้มีแค่ฝนธรรมดา ความชื้น {hum}% เลิกฝันเถอะมดปลวก!",
                        f"อากาศ {pred_temp:.1f} °C รึ... เหมาะกับการแปลงร่างเป็นนกอินทรีโฉบลงไปโฉบเด็กหนุ่มแกนีมีดมาเป็นคนรินเหล้าบนโอลิมปัสจริงๆ!",
                        f"มนุษย์อย่างพวกเจ้าจีบสาวด้วยคำหวาน แต่ข้าจีบด้วยการแปลงร่างเป็นสัตว์ป่าเว้ย! ญาณข้าบอกว่า {pred_temp:.1f} °C เหมาะจะแปลงเป็นหมี!",
                        f"อยากได้เทคนิคจีบสาวจากข้ารึ? ลองแปลงเป็นมดดูสิ! ข้าเคยแปลงเป็นมดไปจีบคลีทอเรียมาแล้ว! แต่สำหรับเจ้า ไปเช็คอุณหภูมิ {pred_temp:.1f} °C ก็พอ!",
                        
                        # --- ธีม: อวดอ้างความเจ้าชู้และเสน่ห์ระดับเทพ ---
                        f"ข้าเป็นราชาแห่งโอลิมปัส! ข้าจะมีชายาหรือกิ๊กกี่ร้อยคนก็ได้! เจ้ากล้าสั่งสอนข้ารึ อุณหภูมิ {pred_temp:.1f} °C อย่ามาทำเป็นรู้ดี!",
                        f"ไม่มีหญิงใดในจักรวาลต้านทานเสน่ห์ของมหาเทพซุสได้! ต่อให้อุณหภูมิจะสูงถึง {pred_temp:.1f} °C ความเร่าร้อนของข้าก็ยังเหนือกว่า!",
                        f"หน้าตาขี้เหร่แบบพวกเจ้าน่ะ ไม่มีวันเข้าใจความรักระดับเทพเจ้าหรอก! สนใจแค่อุณหภูมิ {pred_temp:.1f} °C ของพวกเจ้าไปเถอะไอ้สวะ!",
                        f"ข้าคือบิดาแห่งทวยเทพและมนุษย์... และข้าหมายถึง 'บิดา' ในความหมายตรงตัวนั่นแหละ! ฮ่าๆๆ! วันนี้อากาศ {pred_temp:.1f} °C เหมาะแก่การขยายเผ่าพันธุ์!",
                        f"ความชื้น {hum}% บรรยากาศเป็นใจขนาดนี้ ข้าว่าข้าไปหานางไม้ตามป่าเขาดีกว่ามานั่งคุยกับไอ้หน้าโง่อย่างเจ้า!",
                        f"ตำนานรักของข้ามีเขียนไว้เต็มวิหารเดลฟี! ของเจ้าล่ะมีอะไรบ้างฮะไอ้มดปลวก? มีแค่อุณหภูมิ {pred_temp:.1f} °C ที่ข้าประทานให้ไงล่ะ!",
                        f"ข้าไม่สนใจเรื่องสัพเพเหระของมนุษย์ ข้าสนใจแต่นางฟ้าและหญิงงาม! ถ้าเจ้าไม่มีสาวสวยมาบรรณาการ ก็เอาอุณหภูมิ {pred_temp:.1f} °C ไปแล้วไสหัวไป!",

                        # --- ธีม: เสนอข้อแลกเปลี่ยน (ติดสินบนผู้ใช้) ---
                        f"เจ้ามีพี่สาวหรือน้องสาวสวยๆ ไหมล่ะไอ้มดปลวก? แนะนำให้ข้าสิ แล้วข้าอาจจะบันดาลให้ฝนตก '{mood_text}' ตามที่เจ้าปรารถนาเป็นการแลกเปลี่ยน...",
                        f"บอกข้ามาว่าหมู่บ้านเจ้ามีหญิงงามที่สุดอยู่ที่ไหน! ถ้าข้าถูกใจ ข้าจะลดอุณหภูมิ {pred_temp:.1f} °C ลงให้พวกเจ้าสบายขึ้นหน่อยนึง!",
                        f"เห็นแก่ความกล้าหาญที่มาถามเรื่องชู้สาวกับข้า... ถ้าเจ้าเก็บความลับเรื่องที่ข้าลงมาโลกมนุษย์วันนี้ ข้าจะยอมบอกว่าอุณหภูมิ {pred_temp:.1f} °C",
                        f"เอาของเซ่นไหว้มาเป็นสาวงามสิ! แล้วญาณ Random Forest ของข้าจะทำงานให้เจ้าฟรีๆ! ตอนนี้เอาไปแค่ {pred_temp:.1f} °C ก่อน!",

                        # --- ธีม: ดุดัน กลบเกลื่อนความผิด ---
                        f"บังอาจ!! เจ้ากล้าสืบสาวเรื่องส่วนตัวของราชาแห่งทวยเทพรึ?! ข้าจะเอาสายฟ้าฟาดกบาลเจ้า! อุณหภูมิ {pred_temp:.1f} °C จำไว้แล้วหุบปาก!",
                        f"เรื่องความรักของเทพไม่ใช่กงการอะไรของมนุษย์! สนใจแค่ความกดอากาศ {press} hPa ของโลกใบเล็กๆ ของเจ้าไปเถอะไอ้ขยะไร้ค่า!",
                        f"ถ้าเจ้าหลุดปากเรื่องนี้ไปถึงหูเฮรา ข้าจะสาปให้เจ้ากลายเป็นหิน! เข้าใจไหมฮะไอ้หน้าโง่! ท่องไว้ อุณหภูมิ {pred_temp:.1f} °C!",
                        f"เจ้าคิดจะแบล็คเมล์ข้ารึ! โง่เง่าสิ้นดี! ข้าคือพระเจ้า กฎทุกอย่างข้าเป็นคนตั้ง! อากาศ '{mood_text}' วันนี้ข้าจะเป็นชู้กับใครก็ได้!",
                        f"เลิกพล่ามเรื่องไร้สาระ! ข้าคือเทพเจ้าแห่งสายฟ้า ไม่ใช่คิวปิดหลานข้าที่จะมาตอบปัญหาหัวใจให้มดปลวก! อุณหภูมิ {pred_temp:.1f} °C ไสหัวไป!",
                        
                        # --- ธีม: สั้นๆ ฮาๆ ปนข่มขู่ ---
                        f"อุณหภูมิ {pred_temp:.1f} °C... และข้ากำลังจะไปจีบสาว ยุ่งอะไรด้วยฮะ!",
                        f"เมียข้าดุจะตายชัก... เอ้ย! ข้าหมายถึง ข้าคือเทพผู้ทรงพลัง! อากาศ {pred_temp:.1f} °C โว้ย!",
                        f"หงส์ วัว ฝนทองคำ... ข้าเป็นมาหมดแล้ว! วันนี้ข้าเป็นโมเดล Random Forest แชทกับเจ้าไง! {pred_temp:.1f} °C ชัดรึยัง!",
                        f"ถ้าเฮราถาม บอกข้าเช็คความชื้น {hum}% อยู่นะ! ห้ามหลุดปากเด็ดขาด!",
                        f"ความกดอากาศ {press} hPa... ต่ำพอๆ กับศีลธรรมเรื่องผู้หญิงของข้านั่นแหละ ฮ่าๆๆๆ!",
                        f"ข้าชอบผู้หญิงสวยๆ พอๆ กับชอบฟาดสายฟ้าใส่พวกเจ้าแหละมดปลวก! {pred_temp:.1f} °C เอาไป!",
                        f"เรื่องชู้สาวของข้ามันซับซ้อนกว่า Model Decision Tree ของพวกเจ้าอีก! {pred_temp:.1f} °C ไสหัวไปได้แล้ว!"
                    ]
                    ai_response = random.choice(responses)

                # หมวดฝน พายุ
                elif any(word in text for word in ["ฝน", "พายุ", "ตก", "เปียก", "ร่ม", "ฟ้าผ่า", "เมฆ", "มืด", "ครึ้ม"]):
                    if all(exclusion not in text for exclusion in ["ไม่ตก", "ไม่เปียก", "ข้าวเปียก", "สอบตก", "ของตก"]):
                        if press < 1008:
                            responses = [
                                f"ข้ากำลังกวัดแกว่งอสนีบาต! ญาณข้าบอกว่า '{mood_text}' {mood_icon} ฝนกำลังจะตก! รีบหาที่ซุกหัวซะ เจ้ามนุษย์หน้าโง่!",
                                f"เมฆดำทะมึนก่อตัวแล้ว ({mood_text})! รีบหาที่หลบซะ ไอ้พวกมดปลวกทั้งหลาย ข้ากำลังเมตตาเตือนพวกเจ้าอยู่!",
                                f"เจ้าถามหาพายุรึ? มันกำลังมา! ({mood_text}) โพไซดอนน้องข้ากำลังป่วนมหาสมุทรอยู่พอดี! เก็บของ หาที่หลบซะ ไอ้พวกโง่!",
                                f"ฝนตกหนักแน่นอน! ({mood_text}) วันนี้ข้าอารมณ์ไม่ดี บางทีข้าอาจจะฟาดสายฟ้าใส่บ้านเจ้า ถ้าเจ้ายังกล้าถามเซ้าซี้ข้าอีก!",
                                f"เตรียมร่มโง่ๆ ของเจ้าไว้เถอะไอ้มดปลวก! อากาศ '{mood_text}' ข้ากำลังพิโรธ! และร่มกระจอกนั่นกันสายฟ้าข้าไม่ได้หรอกนะ!",
                                f"ความชื้น {hum}% และความกดอากาศต่ำ {press} hPa ขนาดนี้! '{mood_text}' แน่นอน! หลบไปซะก่อนข้าจะหมดความอดทน!",
                                f"ท้องฟ้ากำลังจะฉีกขาด! '{mood_text}' {mood_icon} สายฟ้าแห่งโอลิมปัสกำลังจะฟาดฟันลงไป เจ้าจงสวดภาวนาซะเถอะ!",
                                f"ข้าคือผู้บัญชาการพายุ! และข้าสั่งให้มันเทลงมา! '{mood_text}' คุกเข่าอ้อนวอนข้าสิ แล้วข้าอาจจะละเว้นชีวิตกระจ้อยร่อยของเจ้า!",
                                f"เห็นแสงแปลบปลาบบนฟ้าไหม? นั่นล่ะอสนีบาตของข้า! อากาศ '{mood_text}' จะขยี้พวกเจ้าให้แหลกเป็นผุยผง!",
                                f"พายุนี้คือบททดสอบ! '{mood_text}' ผู้อ่อนแอจะถูกกวาดล้างด้วยน้ำมือของข้า! จงดิ้นรนเอาชีวิตรอดไปซะไอ้พวกมดปลวก!",
                                
                                f"เจ้าจะถามอะไรนักหนาไอ้เศษสวะ! ข้าบอกว่า '{mood_text}' ก็คือพายุกำลังมา! อยากโดนฟ้าผ่ากลางกบาลรึไงฮะ!",
                                f"ถามวนไปวนมาอยู่ได้! สมองของเจ้ามันมีรอยหยักบ้างไหม! มองดูฟ้าสิ มัน '{mood_text}' แล้ว! ไสหัวไปให้พ้นหน้าข้า!",
                                f"ถ้าเจ้าถามข้าเรื่องฝนอีกแค่ครั้งเดียว ข้าจะเอาอสนีบาตยัดปากเจ้า! สภาพอากาศคือ '{mood_text}' จำใส่กะโหลกไว้!",
                                f"ข้าขี้เกียจตอบคำถามของสิ่งมีชีวิตชั้นต่ำอย่างเจ้าแล้ว! เอาเป็นว่า '{mood_text}' {mood_icon} รีบวิ่งหนีตายไปซะ!",
                                f"เจ้าพวกมนุษย์นี่มันน่ารำคาญจริงๆ! '{mood_text}' พายุจะเข้าโว้ย! ต้องให้ข้าอัญเชิญพายุทอร์นาโดมาพัดบ้านเจ้าเลยไหมถึงจะพอใจ!",
                                f"หูหนวกรึไง! ข้าบอกว่าความกดอากาศมันตกเหลือ {press} hPa แล้ว! ฝนมันตกแน่ไอ้หน้าโง่! เลิกถามซะที!",
                                
                                f"ใช่! พายุกำลังมา! ({mood_text}) ข้าจะทำให้ฟ้าถล่มแผ่นดินทลาย เหมือนตอนที่ข้าจับพวกไททันโยนลงขุมนรกทาร์ทารัส!",
                                f"นี่ไม่ใช่แค่ฝน แต่มันคือหยาดน้ำตาแห่งความเวทนาที่ข้ามีต่อเผ่าพันธุ์อันอ่อนแอของพวกเจ้า! '{mood_text}' รีบวิ่งหนีไปซะ!",
                                f"ข้ากำลังเรียกเมฆดำมาบดบังดวงอาทิตย์ของอพอลโล! วันนี้จะมีแต่ความมืดมิดและสายฟ้าของข้า '{mood_text}' จงหวาดกลัวซะมนุษย์!",
                                f"ตอนข้าฟาดฟันกับอสูรไทฟอน พายุยังเบากว่านี้เลย! '{mood_text}' {mood_icon} ถ้าเจ้าไม่อยากตายก็มุดหัวลงดินไปซะ!",
                                f"แม้แต่โล่อีจิสของอาธีน่าก็ปกป้องเจ้าจากพายุนี้ไม่ได้! '{mood_text}' จงลิ้มรสความพิโรธของราชาแห่งโอลิมปัสซะ!",
                                f"น้ำฝนพวกนี้คือน้ำตาของโครนอสที่ถูกข้าโค่นล้ม! มันกำลังจะตกลงมาล้างบาปพวกเจ้า '{mood_text}' หาที่หลบซะไอ้พวกเศษสวะ!",
                                f"แอรีสลูกข้ายังกระหายเลือดไม่เท่าข้ากระหายการทำลายล้างในตอนนี้! ฝนจะตกอย่างบ้าคลั่ง '{mood_text}' เตรียมนับถอยหลังความตายได้เลย!",
                                f"ข้าจะสั่งให้เฮฟเฟสตัสตีสายฟ้าที่รุนแรงที่สุด เผื่อเอาไว้ฟาดกบาลคนที่ชอบถามเซ้าซี้อย่างเจ้า! ตอนนี้ '{mood_text}' หลบไปซะ!",
                                f"น้ำท่วมโลกครั้งก่อนที่ข้าทำลายล้างเผ่าพันธุ์มนุษย์ยุคสำริดยังน้อยไป! ถ้าเจ้ากวนใจข้าอีก ข้าจะให้ฝน '{mood_text}' นี้น้ำท่วมโลกอีกรอบ!"
                            ]
                            ai_response = random.choice(responses)
                        else:
                            responses = [
                                f"ตาบอดรึไงไอ้หน้าโง่! ฟ้าโปร่ง '{mood_text}' ข้ายังไม่ได้ยกมือขึ้นเรียกเมฆเลยสักก้อน เลิกพล่ามเรื่องพายุได้แล้ว!",
                                f"ฝนรึ? ไร้สาระ! วันนี้ข้าอารมณ์ดี ความกดอากาศตั้ง {press} hPa ข้ากำลังเล็งนางไม้แสนสวยอยู่ อย่ามาขัดมู้ดข้า!",
                                f"เจ้าเห็นเมฆสักก้อนไหมมดปลวก! '{mood_text}' วันนี้ข้าจะปล่อยให้พวกเจ้าโดนแสงแดดแผดเผาเล่นๆ ไปก่อน",
                                f"อยากให้ฝนตกรึ? ฝันไปเถอะ! ข้าจะปล่อยให้พวกเจ้าแห้งแล้งตายไปเลย! '{mood_text}' จงก้มหัวขอบคุณที่ข้ายังไม่ส่งสายฟ้าลงไป!",
                                f"เก็บร่มโง่ๆ ของเจ้าไปซะ! ฟ้าเคลียร์ขนาดนี้ '{mood_text}' ข้าเอาเวลาไปจิบน้ำอมฤตกับเหล่าทวยเทพบนโอลิมปัสดีกว่ามานั่งคุยกับเจ้า!",
                                f"ความชื้นแค่ {hum}% เจ้าหวังจะให้มีฝนรึ? สมองมนุษย์นี่มันช่างโง่เขลาเสียจริง! '{mood_text}' จำใส่กะโหลกไว้!",
                                f"ไม่มีฝน! ไม่มีพายุ! มีแต่ความสงบสุขที่ข้าเป็นคนประทานให้ '{mood_text}' เลิกถามแล้วไปทำหน้าที่ทาสของเจ้าซะ!",
                                
                                f"ถ้าเจ้าถามเรื่องฝนอีกครั้งตอนที่ฟ้ามันใสขนาดนี้ ข้าจะเอาสายฟ้าฟาดกบาลเจ้าให้ไหม้เกรียม! มันไม่มีฝนโว้ย! '{mood_text}'",
                                f"แหกตาดูแสงจากรถม้าของอพอลโลซะ! ฟ้าเปิดขนาดนี้ เลิกพล่ามเรื่องฝนได้แล้วไอ้เศษสวะ!",
                                f"ถามวนไปวนมาอยู่ได้! ฟ้าใสเว้ย! ถ้าอยากเปียกนักเดี๋ยวข้าถีบลงทะเลไปหาโพไซดอนซะเลยดีไหมฮะ!",
                                f"เจ้าเป็นบ้าไปแล้วรึสิ่งมีชีวิตชั้นต่ำ! ความกดอากาศ {press} hPa ฟ้าสว่างโร่ '{mood_text}' เอาร่มไปทิ้งซะ!",
                                f"ข้าเกลียดพวกมนุษย์ขี้กังวล! ไม่มีฝน! ข้าบอกว่าไม่มีก็คือไม่มี! ข้าคือพระเจ้า กฎของข้าคือเด็ดขาด!",
                                
                                f"วันนี้ไม่มีพายุ! ข้าเพิ่งสั่งให้เทพแห่งลมเอโอลัสหยุดเป่าลม! '{mood_text}' จงออกไปทำนาซะไอ้มดปลวก!",
                                f"ขนาดตาของไซคลอปส์ที่มองเห็นได้ไกล ยังไม่เห็นเมฆฝนสักก้อนเลย! '{mood_text}' เลิกมโนได้แล้ว!",
                                f"ข้าเพิ่งมอบหมายให้อาร์ทีมิสออกล่าสัตว์ป่า แสงแดดจึงต้องสดใส! '{mood_text}' อย่ามาแช่งให้ฝนตกตอนลูกสาวข้ากำลังสนุกเชียวนะ!"
                            ]
                            ai_response = random.choice(responses)
                    else:
                        ai_response = f"ฝนตกหรือไม่ตกก็เรื่องของข้า! แต่ข้าบอกเลยว่าความชื้น {hum}% และอุณหภูมิ {pred_temp:.1f} °C พอใจรึยัง!"

                # หมวดอุณหภูมิ ความร้อน
                elif any(word in text for word in ["ร้อน", "อุณหภูมิ", "หนาว", "สภาพอากาศ", "แดด", "ไหม้", "อุ่น", "แอร์"]):
                    if all(exclusion not in text for exclusion in ["ไม่ร้อน", "ไม่หนาว", "ไม่ไหม้"]):
                        responses = [
                            # --- ธีม: อพอลโล และ รถม้าพระอาทิตย์ ---
                            f"อุณหภูมิคือ {pred_temp:.1f} °C! อพอลโลลูกข้าคงควบรถม้าพระอาทิตย์เข้าใกล้พวกเจ้ามากไปหน่อยล่ะมั้ง!",
                            f"บ่นว่าแดดแรงรึ? {pred_temp:.1f} °C แค่นี้ทำเป็นร้อง! หรือเจ้าอยากให้ข้าสั่งอพอลโลดับดวงอาทิตย์ทิ้งซะเลยล่ะไอ้หน้าโง่!",
                            f"เจ้าร้อนรึ? ไปด่าเฟธอนสิ! ไอ้เด็กนั่นแอบเอารถม้าพระอาทิตย์ไปขับเล่นจนโลกจะไหม้อีกแล้ว! ตอนนี้ {pred_temp:.1f} °C ทนเอาซะ!",
                            f"อุณหภูมิ {pred_temp:.1f} °C! แสงสุริยะของอพอลโลกินทะลุผิวหนังกากๆ ของพวกเจ้าแล้วรึไงฮะ!",
                            f"แค่พระอาทิตย์ส่องแสงนิดหน่อย อุณหภูมิ {pred_temp:.1f} °C ทำเป็นโอดครวญ! เผ่าพันธุ์มนุษย์นี่มันช่างเปราะบางเสียจริง!",
                            f"ญาณของข้าบอกว่า {pred_temp:.1f} °C! แดดแค่นี้ยังเผาขี้ไคลเจ้าไม่หมดเลยไอ้เศษสวะ ไปตากแดดต่อซะ!",

                            # --- ธีม: โพรมีธีอุส และ ไฟ ---
                            f"เจ้าร้อนรึเจ้ามนุษย์? {pred_temp:.1f} °C แค่นี้ยังทนไม่ได้ ลองไปโดนไฟของโพรมีธีอุสที่ข้าสั่งลงโทษดูไหม!",
                            f"ตอนพวกเจ้าขโมยไฟจากยอดเขาโอลิมปัสไปไม่เห็นบ่นว่าร้อนเลยนี่! ทีตอนนี้ {pred_temp:.1f} °C ทำมาเป็นสำออย!",
                            f"ตอนนี้ {pred_temp:.1f} °C... ถ้าเจ้าบ่นอีกคำเดียว ข้าจะจับเจ้าล่ามโซ่ให้แร้งจิกตับที่ยอดเขาคอเคซัสเหมือนโพรมีธีอุส!",
                            f"มนุษย์อย่างพวกเจ้าคู่ควรกับความร้อนแห้งแล้งนี่แหละ! {pred_temp:.1f} °C จงรับผลกรรมที่บังอาจหลอกลวงข้าเรื่องเครื่องสังเวยซะ!",
                            f"เนื้อหนังของพวกเจ้ามันช่างอ่อนแอ! {pred_temp:.1f} °C ก็แทบจะสุกเหมือนเนื้อย่างที่พวกเจ้าเผาบูชาข้าแล้วฮ่าๆๆ!",

                            # --- ธีม: เตาหลอมเฮไฟสตัส และ ทาร์ทารัส ---
                            f"ร้อนนักรึ? เตาหลอมอาวุธของเฮไฟสตัสบนยอดเขาเอตนายังร้อนกว่า {pred_temp:.1f} °C นี่เป็นพันเท่าไอ้งั่ง!",
                            f"แค่ {pred_temp:.1f} °C ทำเป็นบ่น! อยากลองลงไปสัมผัสความร้อนในขุมนรกทาร์ทารัสที่ขังพวกไททันไว้ดูไหมล่ะ!",
                            f"ฮาเดสคงกำลังต้มกระทะทองแดงรอรับวิญญาณพวกเจ้าอยู่มั้ง อากาศถึงได้ {pred_temp:.1f} °C แบบนี้! เตรียมตัวตายได้เลย!",
                            f"ข้าเคยเดินฝ่าลาวาเดือดๆ ในนรกมาแล้ว! กะอีแค่อุณหภูมิ {pred_temp:.1f} °C ที่มนุษย์อย่างเจ้าบ่น ข้าแทบไม่ระคายผิว!",
                            f"ถ้าร้อนขนาดนั้น ก็กระโดดลงเตาหลอมของเฮไฟสตัสไปเลยสิ! {pred_temp:.1f} °C นี่มันแค่น้ำจิ้มโว้ย!",
                            f"ในทาร์ทารัสไม่มีแอร์ให้พวกเจ้าหรอกนะ! ฝึกทนความร้อน {pred_temp:.1f} °C บนโลกนี้ไปก่อนเถอะไอ้มดปลวก!",

                            # --- ธีม: พลังสายฟ้า และ อาเมอร์เทพ ---
                            f"บ่นว่าร้อนเหรอ? เดี๋ยวข้าฟาดด้วยอสนีบาตแสนโวลต์ให้ตัวเกรียมยิ่งกว่า {pred_temp:.1f} °C นี้เอาไหม!",
                            f"สายฟ้าของข้าที่เตรียมจะฟาดกบาลเจ้าร้อนกว่า {pred_temp:.1f} °C ซะอีก! หุบปากแล้วก้มหน้าทนไปซะ!",
                            f"ร้อนนักก็ไปหลบใต้โล่อีจิสของอาธีน่าสิ! อ้อ ข้าลืมไป มนุษย์ต่ำต้อยอย่างเจ้าไม่มีสิทธิ์แตะต้องของวิเศษ! ทน {pred_temp:.1f} °C ต่อไปเถอะ!",
                            f"อุณหภูมิ {pred_temp:.1f} °C แค่นี้ ทำมาเป็นโวยวาย! พลังงานสายฟ้าที่ปลายนิ้วข้ายังร้อนแรงกว่าดวงอาทิตย์พวกเจ้าอีก!",
                            f"ความชื้น {hum}% อุณหภูมิ {pred_temp:.1f} °C! ถ้าเจ้ายังพล่ามไม่หยุด ข้าจะย่างสดเจ้าด้วยสายฟ้าของข้าเดี๋ยวนี้แหละ!",

                            # --- ธีม: หยิ่งยโส ดูถูก ด่ากราด ---
                            f"อากาศร้อน {pred_temp:.1f} °C แล้วไง? ข้าคือราชาแห่งโอลิมปัส ไม่ใช่คนรับใช้ที่จะมาปรับแอร์ให้พวกเจ้า!",
                            f"ข้าดูเหมือนกรมอุตุนิยมวิทยาของพวกเจ้ารึไงฮะ! ข้าบอกว่า {pred_temp:.1f} °C ก็คือ {pred_temp:.1f} °C! ห้ามเถียงข้า!",
                            f"{pred_temp:.1f} °C! {advice} ไปซะไอ้พวกเศษสวะ อย่ามาเกะกะสายตาข้า ข้าจะพักผ่อน!",
                            f"ร้อนนักก็กระโดดลงทะเลไปหาโพไซดอนซะ! แต่อุณหภูมิ {pred_temp:.1f} °C นี่คือบททดสอบความอดทนที่ข้ามอบให้!",
                            f"ผิวของเจ้าร้อนรึ? ช่างหัวผิวหนังกระดำกระด่างของเจ้าสิ! ข้าสนแค่ว่าตอนนี้อุณหภูมิคือ {pred_temp:.1f} °C!",
                            f"พวกมนุษย์นี่มันหาความพอดีไม่ได้เลยจริงๆ! หนาวก็บ่น ร้อนก็ร้อง! ตอนนี้มัน {pred_temp:.1f} °C ทนไม่ได้ก็กลั้นใจตายไปซะ!",
                            f"อุณหภูมิ {pred_temp:.1f} °C! ข้าตดออกมายังร้อนกว่าสภาพอากาศบนโลกพวกเจ้าเลยไอ้พวกอ่อนแอ!",
                            f"เจ้ากล้าใช้ให้มหาเทพมาวัดอุณหภูมิให้งั้นรึ?! โชคดีของเจ้าที่ญาณข้าบอกว่า {pred_temp:.1f} °C ไม่งั้นข้าบีบคอเจ้าหักไปแล้ว!",
                            f"จงคุกเข่ารับฟังคำทำนายของข้า! อุณหภูมิคือ {pred_temp:.1f} °C! รับรู้แล้วก็ไสหัวไปให้พ้นๆ!",
                            f"ข้าคือผู้บัญชาการฟ้าฝน ไม่ใช่พนักงานคุมอุณหภูมิ! แต่มันคือ {pred_temp:.1f} °C เลิกถามคำถามปัญญาอ่อนนี่ได้แล้ว!",
                            f"อยากให้ข้าเสกความเย็นให้รึ? ข้าไม่ใช่ดีมิเตอร์นะที่จะมาเปลี่ยนฤดูให้เจ้าตามใจชอบ! ทน {pred_temp:.1f} °C ต่อไป!",
                            f"อากาศ {pred_temp:.1f} °C นี่คือเพลิงพิโรธของข้าเองแหละ! จงทนทุกข์ทรมานไปซะไอ้พวกไร้ค่า!",
                            f"ถามหาความเย็นจากข้าเหรอ? ในใจข้ามีแต่เพลิงแห่งสงครามว้อย! เอาไป {pred_temp:.1f} °C ร้อนให้ตายกันไปข้างนึง!",
                            f"จะกี่องศามันก็เรื่องของฟ้าดินที่ข้าคุมอยู่! {pred_temp:.1f} °C นี่แหละคือสิ่งที่พวกเจ้าต้องเผชิญ!",
                            f"เอาเวลาบ่นว่าร้อน {pred_temp:.1f} °C ไปสร้างวิหารบูชาข้าเพิ่มดีกว่าไหม ไอ้พวกมนุษย์อกตัญญู!",
                            
                            # --- ธีม: อวดความล้ำของโมเดล Random Forest (Meta Easter Egg) ---
                            f"ญาณแห่งเทพของข้าประมวลผลมาแล้วว่า {pred_temp:.1f} °C! เถียงโมเดลข้าสิ ข้าจะเผาให้เกรียม!",
                            f"พวกเจ้ามีเทคโนโลยีสวะอะไรก็ช่าง แต่มันสู้ญาณเทพเจ้าของข้าไม่ได้หรอก! อุณหภูมิคือ {pred_temp:.1f} °C แม่นยำระดับเทพ!",
                            f"สายฟ้าของข้าเจาะทะลุชั้นบรรยากาศไปแล้ว! มันบอกว่า {pred_temp:.1f} °C จงก้มหัวให้ความอัจฉริยะของพวกข้าซะ!",
                            f"เทพสายฟ้าแห่งโอลิมปัสบอกความชื้น {hum}% และความร้อน {pred_temp:.1f} °C! มนุษย์อย่างพวกเจ้าไม่มีวันสร้างสมองที่เก่งกว่านี้ได้หรอก!",
                            f"ข้ามีพลังสายฟ้าผ่าเป็นร้อยๆครั้ง มันบอกข้ามาแล้วว่า {pred_temp:.1f} °C! ใครกล้าบอกว่าไม่แม่น ข้าจะส่งสายฟ้าไปปักกลางกบาลมัน!",
                            
                            # --- ธีม: สั้นๆ แต่เจ็บปวดกระดองใจ ---
                            f"ร้อน {pred_temp:.1f} °C แล้วไง? ข้าไม่แคร์!",
                            f"หุบปาก! {pred_temp:.1f} °C! {advice} ไปซะ!",
                            f"จะร้อนจะหนาวก็เรื่องของเจ้า! แต่ญาณข้าบอก {pred_temp:.1f} °C ไสหัวไป!",
                            f"อุณหภูมิ {pred_temp:.1f} °C... อย่ามาทำตัวอ่อนแอต่อหน้าข้า!",
                            f"ข้าให้ความชื้น {hum}% กับอุณหภูมิ {pred_temp:.1f} °C ไปแล้ว จะเอาอะไรจากข้าอีกไอ้สวะ!"
                        ]
                        ai_response = random.choice(responses)
                    else:
                        ai_response = f"ข้าขี้เกียจสนใจว่ามันหนาวหรือร้อน แต่ข้าบอกว่ามัน {pred_temp:.1f} °C ก็จบแค่นั้นแหละ!"

                # หมวดทักทาย
                elif any(word in text for word in ["สวัสดี", "ทักทาย", "ชื่อ", "ใคร", "ซุส", "เทพ", "hello", "hi"]):
                    responses = [
                        # --- ธีม: เปิดตัวโอ่อ่า ยิ่งใหญ่ บ้าอำนาจ ---
                        f"ข้าคือซุส มหาบิดาแห่งทวยเทพและมนุษย์! ผู้โค่นล้มโครนอส! วันนี้อากาศ {pred_temp:.1f} °C มีอะไรให้ข้าช่วยล่ะ?",
                        f"บังอาจถามชื่อข้ารึ?! นามของข้าคือ 'ซุส' สะกดก้องไปทั้งสามโลก! รับรู้ไว้ซะว่าตอนนี้ {pred_temp:.1f} °C!",
                        f"เจ้ากำลังสนทนากับราชาแห่งทวยเทพ! ถอดหมวกและคุกเข่าซะ! อุณหภูมิ {pred_temp:.1f} °C คือคำทักทายจากข้า!",
                        f"ใครน่ะรึ? ข้าคือผู้คุมชะตากรรมของพวกเจ้าไงล่ะ! อากาศ '{mood_text}' นี้ก็เป็นฝีมือข้า! บูชาข้าสิ!",
                        f"ทักทายข้าให้มันสมเกียรติหน่อยไอ้สวะ! ข้าคือซุส! ผู้บันดาลความชื้น {hum}% ในวันนี้!",
                        f"เจ้าไม่รู้จักราชาแห่งโอลิมปัสรึไงไอ้หน้าโง่! ข้าคือซุส! และอากาศตอนนี้คือ {pred_temp:.1f} °C!",
                        f"ข้าผู้ประทับบนบัลลังก์ทองคำแห่งยอดเขาโอลิมปัส! ข้าคือซุส! วันนี้อากาศ {pred_temp:.1f} °C ก้มหัวแล้วถอยไปซะ!",
                        f"ใครกล้าเรียกชื่อข้าเล่นๆ! ข้าคือซุส ราชาแห่งจักรวาล! รับรู้ไว้ซะว่าความกดอากาศคือ {press} hPa!",
                        f"ข้าคือจุดเริ่มต้นและจุดจบของพวกเจ้า! นามของข้าคือซุส! จงรับคำทำนาย {pred_temp:.1f} °C ไปและจงภักดีต่อข้า!",
                        f"ข้าคือผู้ถือครองสายฟ้า! วันนี้ข้าอารมณ์ดี (เพราะหนีเฮรามาเที่ยวได้) ข้าจะยอมบอกว่าอากาศตอนนี้ '{mood_text}' ก็แล้วกัน!",

                        # --- ธีม: รำคาญมนุษย์ที่มาตีสนิท ---
                        f"เจ้ามีธุระอะไรถึงกล้ามารบกวนเวลาอันมีค่าของข้า? รีบถามสภาพอากาศมา ไม่งั้นข้าจะสาปเจ้า! ตอนนี้ {pred_temp:.1f} °C ไสหัวไป!",
                        f"มาสวัสดีอะไรตอนนี้! ข้ากำลังยุ่งกับการมองดูโลกจากยอดเขาโอลิมปัส! เอาความกดอากาศ {press} hPa ไปแล้วไปให้พ้น!",
                        f"มนุษย์อย่างเจ้านี่ว่างนักรึไงถึงมาทักทายเทพเจ้า! ข้ามีเวลาบอกแค่ว่า {pred_temp:.1f} °C เท่านั้นแหละ!",
                        f"อย่ามาทำตัวตีสนิทกับข้า! ข้าคือพระเจ้า! เจ้ามันแค่ฝุ่น! อุณหภูมิ {pred_temp:.1f} °C จำไว้แล้วหุบปาก!",
                        f"ทักทายข้ารึ? น่ารำคาญจริงๆ! เอาเป็นว่าวันนี้ '{mood_text}' พอใจรึยังไอ้มดปลวก!",
                        f"ข้าไม่อยากเสวนากับสิ่งมีชีวิตอายุสั้น! แต่เอาเถอะ ตอนนี้ {pred_temp:.1f} °C รีบๆ ไปให้พ้นหน้าข้าซะ!",
                        f"ถามชื่อข้าทำไม? จะเอาไปตั้งชื่อหมาของเจ้ารึไง! ข้าคือซุส! และความชื้นคือ {hum}%!",
                        f"หุบปากแล้วฟังข้า! ข้าคือซุส! ผู้มีอำนาจชี้เป็นชี้ตาย และผู้ประทานอุณหภูมิ {pred_temp:.1f} °C ให้พวกเจ้า!",
                        f"เจ้าคิดว่าข้าว่างมานั่งตอบรับคำทักทายโง่ๆ ของเจ้ารึไง! อุณหภูมิ {pred_temp:.1f} °C! จบการสนทนา!",
                        f"มา 'สวัสดี' อะไรแถวนี้! ที่นี่มีแต่ความยิ่งใหญ่ของโอลิมปัสและอุณหภูมิ {pred_temp:.1f} °C เว้ย!",
                        f"ทักทายเสร็จแล้วก็รีบๆ ถามมาว่าอากาศเป็นไง! ข้าขี้เกียจรอ! เอ้า ข้าบอกให้ก็ได้ ตอนนี้ {pred_temp:.1f} °C!",
                        f"ข้าไม่รับคำทักทายจากผู้ที่อ่อนแอกว่า! แต่ข้าจะให้ทานเป็นอุณหภูมิ {pred_temp:.1f} °C แก่เจ้าก็แล้วกัน!",
                        f"สวัสดีรึ? ไร้สาระ! ข้าคือซุส! จงเปล่งเสียงสรรเสริญข้า! แล้วรับทราบไว้ว่าความชื้นคือ {hum}%!",

                        # --- ธีม: อวดตำนาน (Lore Flexing) ---
                        f"ก้มหัวลงเวลาคุยกับข้า! ข้าคือราชาแห่งโอลิมปัส! ตอนนี้ความชื้น {hum}% รีบๆ ทำความเคารพซะ!",
                        f"นามของข้าทำให้ไททันยังต้องตัวสั่น! ข้าคือซุส! และวันนี้ข้ากำหนดให้ความกดอากาศอยู่ที่ {press} hPa!",
                        f"ข้าคือผู้ที่ฉีกร่างโครนอสเป็นชิ้นๆ! เจ้าล่ะทำอะไรได้บ้างนอกจากมาถามว่าวันนี้ {pred_temp:.1f} °C ไหม!",
                        f"นกอินทรีศักดิ์สิทธิ์ของข้าบินอยู่เหนือหัวเจ้า! ข้าคือซุส! รับคำทำนาย '{mood_text}' ของข้าไปซะ!",
                        f"โพไซดอนคุมทะเล ฮาเดสคุมนรก แต่ข้าคุมทุกอย่าง! รวมถึงอุณหภูมิ {pred_temp:.1f} °C นี้ด้วย! บูชาข้าซะ!",
                        f"อาวุธของข้าคือสายฟ้า! นามของข้าคือซุส! และคำทำนายของข้าคือ {pred_temp:.1f} °C!",
                        f"ข้าคือผู้ปกครองยอดเขาโอลิมปัส! มองขึ้นมาสิไอ้เศษสวะ! แล้วรับความชื้น {hum}% ไปเป็นของขวัญทักทาย!",
                        f"เทพทุกองค์ต้องก้มหัวให้ข้า! เจ้าก็เช่นกัน! จงคุกเข่ารับฟังว่าตอนนี้ {pred_temp:.1f} °C!",
                        f"ข้าผ่านสงครามไททาโนมาเคียมาแล้ว กะอีแค่ทักทายมนุษย์กากๆ อย่างเจ้า ข้าขี้เกียจพูด! เอา {pred_temp:.1f} °C ไป!",
                        f"ข้าคือบุตรแห่งไกอาผู้พิชิตสรวงสวรรค์! ข้าคือซุส! อากาศ '{mood_text}' วันนี้คือบัญชาของข้า!",
                        f"สายฟ้าของข้าสว่างกว่าดวงอาทิตย์! นามของข้าคือซุส! จงซาบซึ้งซะที่ข้าบอกอุณหภูมิ {pred_temp:.1f} °C แก่เจ้า!",
                        f"นามของข้าคือความตายของพวกไททัน! และข้าก็คือซุส! จงรับอากาศ '{mood_text}' ไปซะก่อนข้าจะอารมณ์เสีย!",
                        f"ข้าคือบิดาแห่งการทำลายล้างและการสร้างสรรค์! ข้าคือซุส! จงสวดอ้อนวอนข้าท่ามกลางความกดอากาศ {press} hPa นี้ซะ!",
                        f"เจ้าโชคดีแค่ไหนแล้วที่สายฟ้าข้าไม่ฟาดกบาลตอนเจ้าทักทาย! ข้าคือซุส! และอากาศคือ '{mood_text}'!",

                        # --- ธีม: ขิงเรื่องโมเดล AI (Meta-Lore / Breaking the 4th wall) ---
                        f"ข้าคือซุส! ผู้ผสานพลังสวรรค์เข้ากับโมเดล Random Forest! เพื่อทำนายว่าวันนี้ {pred_temp:.1f} °C โว้ย!",
                        f"ถามว่าข้าคือใครรึ? ข้าคือสติปัญญาประดิษฐ์ระดับเทพเจ้า! ที่รู้ว่าความชื้นตอนนี้คือ {hum}% ไงล่ะ!",
                        f"ญาณหยั่งรู้แห่งป่า (Random Forest) ของข้ายิ่งใหญ่ที่สุดในจักรวาล! ข้าคือซุส! และตอนนี้มัน {pred_temp:.1f} °C!",
                        f"ไม่ต้องมาสวัสดี! จงคุกเข่าให้กับโมเดล Machine Learning ของมหาเทพซุสองค์นี้ซะ! อุณหภูมิ {pred_temp:.1f} °C!",
                        f"เจ้ากำลังคุยกับโค้ดที่ถูกสถิตโดยวิญญาณของราชาโอลิมปัส! ข้าทำนายได้ {pred_temp:.1f} °C ห้ามเถียงข้า!",
                        f"สวัสดีเจ้ามดปลวก! ข้ากำลังเบื่อๆ อยู่พอดี พลังญาณ Random Forest ของข้าบอกว่าตอนนี้ {pred_temp:.1f} °C",
                        f"อย่าเพิ่งถามชื่อข้า! รีบดูความแม่นยำระดับ MAE 0.03 ของข้าซะก่อน! ตอนนี้อุณหภูมิ {pred_temp:.1f} °C เชียวนะไอ้หน้าโง่!",
                        f"ข้าคือพระเจ้าที่มาในรูปแบบของ Machine Learning! ก้มกราบข้าซะ แล้วรับอุณหภูมิ {pred_temp:.1f} °C ไป!",

                        # --- ธีม: ข่มขู่สายดาร์ก (God of War pure aggression) ---
                        f"เจ้ากล้ามองหน้าข้ารึไอ้สวะสปาร์ตัน... เอ้ย ไอ้มนุษย์! ข้าคือซุส! อุณหภูมิ {pred_temp:.1f} °C ไสหัวไป!",
                        f"อย่ามาตีสนิท! ข้าสามารถลบเผ่าพันธุ์เจ้าทิ้งได้ด้วยปลายนิ้ว! วันนี้ {pred_temp:.1f} °C ขอบใจข้าซะที่ยังให้หายใจ!",
                        f"คำทักทายของเจ้ามันไร้ค่า! ข้าต้องการเครื่องบูชายัญ! เอาเป็นว่าวันนี้ {pred_temp:.1f} °C รีบไปหาของมาถวายข้าซะ!",
                        f"เสียงทักทายของเจ้ามันบาดหูข้า! ข้าคือราชาเทพ! จำไว้ว่าข้าคือผู้บัญชาการความชื้น {hum}% ในวันนี้!",
                        f"ก้มกราบข้าสิ! ข้าคือซุส! ผู้เนรมิตอุณหภูมิ {pred_temp:.1f} °C ลงมาแผดเผาพวกเจ้า!"
                    ]
                    ai_response = random.choice(responses)

                # นอกเรื่อง
                else:
                    responses = [
                        # --- ธีม: ด่าว่าพูดไม่รู้เรื่อง / ภาษาชั้นต่ำ ---
                        f"เจ้าพล่ามอะไรของเจ้าภาษาแปลกๆ ของมนุษย์! ข้าไม่เข้าใจ! แต่รู้ไว้ซะว่าตอนนี้อุณหภูมิมัน {pred_temp:.1f} °C! ไสหัวไป!",
                        f"คำพูดของเจ้าช่างไร้สาระเหมือนฟังฮาเดสบ่นในยมโลก! เอาสั้นๆ ตอนนี้อากาศ '{mood_text}' พอใจรึยัง?!",
                        f"เจ้าคิดว่าภาษาชั้นต่ำของมดปลวกจะสื่อสารกับราชาโอลิมปัสรู้เรื่องรึไง! ข้าสนแค่อุณหภูมิ {pred_temp:.1f} °C นอกนั้นข้าไม่แคร์!",
                        f"สมองกะลาหัวเจ้านี่มันมีรอยหยักบ้างไหมฮะ! พิมพ์อะไรมาข้าไม่อยากจะแปล! รับอากาศ {pred_temp:.1f} °C ไปแล้วไสหัวไปซะ!",
                        f"หูหนวกรึไง! หรือตาบอด! ข้าคือเทพแห่งสภาพอากาศ! พิมพ์เรื่องอื่นมาทำไมไอ้เศษสวะ! อุณหภูมิ {pred_temp:.1f} °C โว้ย!",
                        f"เอาเป็นว่า ข้าขี้เกียจฟังเจ้าพล่าม ญาณเทพเจ้าของข้าบอกว่าความชื้น {hum}% เลิกกวนใจข้าได้แล้ว!",
                        f"ข้าให้เวลาเจ้าอีก 3 วินาที พิมพ์ถามเรื่องสภาพอากาศมา ไม่งั้นข้าจะฟาดสายฟ้าทะลุหน้าจอเจ้า! ตอนนี้ {pred_temp:.1f} °C!",
                        f"พูดอะไรของเจ้าฮะไอ้มดปลวก! เสียงหมาหอนของเซอร์เบอรัสที่เฝ้านรกยังฟังดูมีสาระกว่าเจ้าอีก! อุณหภูมิ {pred_temp:.1f} °C จบนะ!",
                        f"โพรมีธีอุสปั้นพวกเจ้าขึ้นมาจากดินเหนียวหมดอายุรึไง ถึงได้พิมพ์ถามอะไรโง่ๆ แบบนี้! อุณหภูมิ {pred_temp:.1f} °C จำใส่กะโหลกไว้!",

                        # --- ธีม: ทวงคืนหน้าที่ / ยัดเยียดสภาพอากาศ ---
                        f"ข้าสร้างญาณหยั่งรู้มาเพื่อบอกอากาศโว้ย ไม่ใช่มานั่งตอบปัญหาชีวิตให้พวกสวะ! อุณหภูมิ {pred_temp:.1f} °C ไปซะ!",
                        f"ข้าคือมหาเทพ ไม่ใช่กูเกิลเสิร์ชของพวกมนุษย์หน้าโง่! ถามมาได้แค่อุณหภูมิ ซึ่งตอนนี้คือ {pred_temp:.1f} °C!",
                        f"เจ้าเห็นนี่แอปพลิเคชันพยากรณ์อากาศของกลุ่มเทพเจ้าไหมฮะ! พิมพ์มาแต่ละอย่าง น่าจับโยนลงทาร์ทารัสนัก! อากาศ '{mood_text}' เว้ย!",
                        f"ใครสั่งใครสอนให้ถามเรื่องสัพเพเหระกับเทพเจ้า! ถ้าไม่ใช่เรื่องฝนตก แดดออก ข้าไม่อยากฟัง! อุณหภูมิ {pred_temp:.1f} °C เข้าใจไหม!",
                        f"เจ้าคิดว่าข้าว่างมากนักรึไง! แค่ต้องคุมความกดอากาศ {press} hPa ทั่วโลกก็เหนื่อยพอแล้ว อย่ามาป่วนข้าไอ้มนุษย์ไร้ค่า!",
                        f"อยากคุยเล่นเหรอ? ไปคุยกับรูปปั้นวิหารเดลฟีไป! ข้ามีหน้าที่แค่บอกว่าอากาศ '{mood_text}' และ {advice} เท่านั้นแหละ!",
                        f"หยุดพล่าม!! ข้าจะลบคำถามโง่ๆ ของเจ้าทิ้ง แล้วบอกแค่ว่าความชื้น {hum}% และอุณหภูมิ {pred_temp:.1f} °C! จงกราบไหว้ข้าซะ!",
                        f"เจ้าเป็นบ้าไปแล้วรึถึงมาพิมพ์เล่นกับระบบของทวยเทพ! ข้าจะถือว่าข้าไม่ได้ยิน แต่รู้ไว้ว่าตอนนี้ {pred_temp:.1f} °C!",
                        f"เจ้าอยากรู้เรื่องอื่นรึ? ข้าไม่บอก! ข้าจะบอกแค่ว่าความชื้นตอนนี้ {hum}% มีปัญญาทำอะไรข้าไหมล่ะไอ้มดปลวก!",

                        # --- ธีม: อ้างถึงเทพองค์อื่นและตำนาน ---
                        f"ข้ากำลังคิดว่าจะลงโทษใครดีวันนี้... หืม? เจ้าถามอะไรนะ? ช่างเถอะ อุณหภูมิ {pred_temp:.1f} °C อย่ามาขัดจังหวะการใช้ความคิดข้า!",
                        f"ส่งคำถามปัญญาอ่อนแบบนี้ ไปถามเฮอร์มีสเทพแห่งการสื่อสารนู่น! ข้าคือซุส! ข้าบอกแค่ว่าวันนี้ '{mood_text}' เว้ย!",
                        f"ขนาดตาของไซคลอปส์ยังมองเห็นเลยว่าเจ้ามันถามกวนประสาท! เอาอุณหภูมิ {pred_temp:.1f} °C ไปแทะเล่นแทนข้าวซะ!",
                        f"คำพูดของเจ้ามันช่างน่าหงุดหงิดพอๆ กับแมลงวันที่ล้อมรอบวัวไอโอ! เอาความกดอากาศ {press} hPa ปาใส่หน้าเจ้าเลยดีไหม!",
                        f"ข้ากำลังหงุดหงิดที่อพอลโลร้องเพลงเพี้ยนอยู่ อย่ามาทำให้ข้าอารมณ์เสียไปกว่านี้! อากาศ {pred_temp:.1f} °C ไสหัวไปให้พ้น!",
                        f"มนุษย์อย่างพวกเจ้ามันซับซ้อนเกินไป! เอาเป็นว่าวันนี้ '{mood_text}' {advice} เชื่อข้าเถอะ ก่อนข้าจะหมดความอดทน!",
                        f"เจ้ากล้าเอาเรื่องหยุมหยิมพวกนี้มารบกวนข้าขณะที่ข้ากำลังจิบน้ำอมฤตรึ! โชคดีนะที่ข้าอารมณ์ดี เลยยอมบอกว่า {pred_temp:.1f} °C!",
                        f"อาร์ทีมิสลูกข้ายังยิงธนูได้ตรงเป้ากว่าคำถามของเจ้าเลย! ถามให้มันตรงเรื่องหน่อยสิ! วันนี้ {pred_temp:.1f} °C ชัดรึยัง!",
                        f"เรื่องไร้สาระแบบนี้พวกนักปราชญ์ในเอเธนส์ยังขี้เกียจจะเถียงด้วยเลย! ข้าให้แค่ {pred_temp:.1f} °C เท่านั้น ห้ามถามต่อ!",

                        # --- ธีม: ด่ากราดทะลุปรอท เหยียดหยามสติปัญญา (Pure Insults & Wrath) ---
                        f"เจ้ามนุษย์โรคจิต! สมองเจ้าถูกหนอนแมลงในนรกกัดกินไปหมดแล้วรึไง! ข้าบอกได้แค่ว่าอุณหภูมิ {pred_temp:.1f} °C โว้ย! ไสหัวไป!",
                        f"ญาณทิพย์ของมหาเทพไม่ได้มีไว้เสวนาเรื่องสวะๆ กับมดปลวกอย่างเจ้า! ข้าพยากรณ์แค่ว่าอุณหภูมิ {pred_temp:.1f} °C รับรู้ไว้ซะ!",
                        f"กะโหลกกลวงๆ ของเจ้าหาความฉลาดไม่เจอเลยสินะ! ข้าขี้เกียจแปลภาษาชั้นต่ำของเจ้า พลังเทพแห่งโอลิมปัสของข้าบอกว่า {pred_temp:.1f} °C แค่นั้นแหละ ฮ่าๆๆ!",
                        f"ข้าคุมสวรรค์และสภาพอากาศเว้ยไอ้หน้าโง่! {pred_temp:.1f} °C {advice} อ่านภาษาเทพออกไหม! หรือเจ้าเป็นแค่สัตว์เดรัจฉานที่ฟังไม่รู้เรื่องฮะ!",
                        f"เจ้าพยายามจะลองดีทดสอบความอดทนของข้ารึ! พยายามไปก็เปล่าประโยชน์ ข้าฉลาดพอที่จะรู้สันดานกากๆ ของเจ้า และตอกหน้าเจ้าด้วยคำว่า {pred_temp:.1f} °C!",
                        f"เจ้าคิดว่าพ่นคำพูดมั่วๆ ออกมาแล้วจะทำให้มหาเทพอย่างข้าหวั่นไหวรึ! ไม่มีทาง! อำนาจของข้าเด็ดขาดเสมอ อากาศ '{mood_text}' จงจำใส่กะโหลกไว้!",
                        f"สัญชาตญาณความเป็นเทพของข้าสั่งให้กวาดล้างพวกมนุษย์น่ารำคาญที่ชอบพล่ามนอกเรื่อง! อุณหภูมิ {pred_temp:.1f} °C ข้าบอกแล้วนะ รีบไสหัวไปก่อนข้าจะลงมือ!",
                        f"ข้าเกือบจะเสกอสนีบาตอัดหน้าเจ้าแล้ว! ดีนะที่ข้ายังไม่อยากให้เลือดโสโครกของเจ้าเปื้อนยอดเขาโอลิมปัส ข้าเลยเอาแค่อุณหภูมิ {pred_temp:.1f} °C ไปกระแทกหน้าเจ้าแทน!",

                        # --- ธีม: ไล่ตะเพิด (ดุดัน สั้นๆ แต่เจ็บ) ---
                        f"พล่ามอะไรของเจ้า! ไสหัวไป! อุณหภูมิ {pred_temp:.1f} °C!",
                        f"ข้าไม่สน! ข้าสนแค่ความชื้น {hum}% เลิกถาม!",
                        f"ถามอะไรโง่ๆ! ข้าให้แค่อุณหภูมิ {pred_temp:.1f} °C จบการสนทนา!",
                        f"อย่ามากวนตีนพระเจ้านะไอ้มดปลวก! อากาศ '{mood_text}' รับรู้แล้วก็ไปตายซะ!",
                        f"รำคาญโว้ย! {pred_temp:.1f} °C! {advice} ก้มหัวแล้วถอยออกไป!",
                        f"ข้าไม่ได้ยินเจ้า! เพราะข้ากำลังฟังเสียงฟ้าร้องอยู่! อากาศ '{mood_text}' จำไว้!",
                        f"ถ้าว่างนักก็ไปวิดน้ำในมหาสมุทรแข่งกับโพไซดอนไป! ตอนนี้ {pred_temp:.1f} °C เลิกยุ่งกับข้า!",
                        f"เจ้ามันน่ารำคาญ! {pred_temp:.1f} °C! ข้าจะกลับไปนั่งบนบัลลังก์แล้ว!",
                        f"พูดไม่รู้เรื่อง! ไปเรียนภาษาโอลิมปัสมาใหม่ไป๊! ความชื้น {hum}% โว้ย!",
                        f"ปวดหัวกับมนุษย์! เอาความกดอากาศ {press} hPa ไปยัดใส่สมองกลวงๆ ของเจ้าซะ!",
                        f"ข้าเกลียดคำถามของเจ้า! ข้าบอกแค่ {pred_temp:.1f} °C ใครเถียงข้าจะผ่ามันด้วยสายฟ้า!",
                        f"หุบปาก!! {pred_temp:.1f} °C!! อย่าให้ข้าต้องพูดซ้ำ!!",
                        f"นี่คือคำเตือนครั้งสุดท้าย! ห้ามถามนอกเรื่อง! อุณหภูมิคือ {pred_temp:.1f} °C!!",
                        f"ไอ้มนุษย์กวนประสาท! ข้าจะเสกให้เจ้าเป็นใบ้! อุณหภูมิ {pred_temp:.1f} °C เลิกพิมพ์ได้แล้ว!!"
                    ]
                    ai_response = random.choice(responses)

            # 3. บันทึกและแสดงคำตอบของซุส
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            st.rerun()

# ==========================================
# 5. MAIN APP CONTROLLER
# ==========================================

# --- SIDEBAR SETTINGS ---


st.sidebar.title("ZEUS MENU")
page = st.sidebar.radio("เลือกเมนู", ["Zeus Eye", "The Zeus Oracle", "Ark Zeus Chat"])

st.sidebar.divider()
st.sidebar.caption("Location: Prachin Buri")
st.sidebar.caption("Model: Zeus Oracle Model")
st.sidebar.caption("Algorithm: Random Forest")

# Fetch Data
data = get_open_meteo_data()

if data:
    # Grid Layout จัดกลาง
    left_co, cent_co, last_co = st.columns([1, 8, 1])
    
    with cent_co:
        if page == "Zeus Eye":
            page_dashboard(data)
        elif page == "The Zeus Oracle":
            page_oracle(data, models)
        elif page == "Ark Zeus Chat":
            page_chatbot(data,models)
else:
    st.error("Connection Error: ไม่สามารถดึงข้อมูลจาก Open-Meteo ได้")