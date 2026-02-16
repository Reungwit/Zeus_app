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

# --- CSS STYLING (Navbar, Sidebar Fix, Centering) ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #FAFAFA; color: #000; }
    
    /* ---------------------------------------------------- */
    /* 1. NAVBAR STYLE */
    /* ---------------------------------------------------- */
     .navbar {
    #     position: fixed;
    #     top: 0;
    #     left: 0;
    #     width: 100%;
        background-color: #fff;
        color: #FFD700;
         padding: 15px;
         text-align: center;
         font-size: 28px;
         font-weight: bold;
         z-index: 9999; /* อยู่สูงกว่าเนื้อหาปกติ */
         border-bottom: 3px solid #FFD700;
          box-shadow: 0 4px 6px rgba(0,0,0,0.3);
     }
    
    /* ดันเนื้อหาลงมาไม่ให้โดน Navbar บัง */
    .main-content { margin-top: 0px; }
    
    /* ---------------------------------------------------- */
    /* 2. SIDEBAR & TOGGLE BUTTON FIX (แก้ปัญหาปุ่มหาย) */
    /* ---------------------------------------------------- */
    
    /* ซ่อนแถบสีรุ้งด้านบนสุดของ Streamlit */
    [data-testid="stDecoration"] {
        display: none;
    }

    /* ปรับแต่งปุ่มกดเปิด Sidebar (Hamburger) ให้ลอยเหนือ Navbar */
    [data-testid="stSidebarCollapsedControl"] {
        z-index: 100000 !important; /* ต้องสูงกว่า Navbar (9999) */
        color: #FFD700 !important; /* สีทอง */
        top: 15 px !important; /* ปรับตำแหน่งให้ตรงกับ Navbar */
        left: 20px !important;
        background-color: transparent !important;
    }
    
    /* ปรับแต่งตัว Sidebar เมื่อเปิดออกมา */
    section[data-testid="stSidebar"] {
        z-index: 100001 !important; /* ต้องสูงกว่าปุ่มและ Navbar */
        top: 5 !important;
        padding-top: 100px !important; /* เว้นที่ด้านบนไม่ให้โลโก้ชนขอบ */
    }

    /* ---------------------------------------------------- */
    /* 3. CENTER CONTENT STYLE */
    /* ---------------------------------------------------- */
    .center-text { text-align: center; }
    div[data-testid="stMetric"] { 
        background-color: #FFF; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #444;
        font-size: 18px;
        text-align: center;
        margin: auto;
    }
    div[data-testid="stMetricLabel"] { justify-content: center; }
    div[data-testid="stMetricValue"] { justify-content: center; color: #132C9C; }
    
    /* ซ่อน Header ปกติของ Streamlit แต่ไม่ซ่อนปุ่ม Sidebar */
    header[data-testid="stHeader"] {
        background-color: transparent;
        z-index: 1; 
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
    # --- ส่วนตรวจสอบ API หน้า Dashboard (วางไว้หลังบรรทัดที่ดึง data) ---

# สมมติว่าตัวแปร data คือตัวที่เก็บผลลัพธ์จาก API
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

# --- ฟังก์ชันคำนวณ Heat Index (วางไว้ช่วงต้นไฟล์) ---
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
        return hi, "🏠 ร้อนชื้น: อยู่ในร่มเถอะ ", "orange"
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
    st.markdown("<h1 class='center-text'>👁️ Zeus Eye</h1>", unsafe_allow_html=True)
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
    st.markdown("<h1 class='center-text'>🔮 The Zeus Oracle </h1>", unsafe_allow_html=True)
    
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
        current_h = current_dt.hour
        
        # สร้างลิสต์เวลา 24 ชม. ข้างหน้า
        next_24_hours = [(current_h + i) % 24 for i in range(24)]
        
        # --- เตรียมข้อมูล (Data Preparation & Logic Fixes) ---
        is_day_list = [1 if 6 <= h <= 18 else 0 for h in next_24_hours]
        
        uv_corrected = []
        for i, uv_val in enumerate(hourly['uv_index'][:24]):
            if is_day_list[i] == 0:
                uv_corrected.append(0.0) # กลางคืน UV ต้อง 0
            else:
                uv_corrected.append(uv_val)

        future_df = pd.DataFrame({
            'temp': hourly['temperature_2m'][:24],
            'humidity': hourly['relative_humidity_2m'][:24],
            'pressure': hourly['surface_pressure'][:24],
            'rain': hourly['rain'][:24],
            'uv': uv_corrected,
            'wind_speed': hourly['wind_speed_10m'][:24],
            'hour': next_24_hours,
            'is_day': is_day_list
        })

        # --- AI Prediction (ทำนายผล) ---
        X_temp = future_df[['humidity', 'pressure', 'rain', 'uv', 'wind_speed', 'hour', 'is_day']]
        pred_temp = models['temp'].predict(X_temp)
        
        X_hum = future_df[['temp', 'pressure', 'rain', 'uv', 'wind_speed', 'hour', 'is_day']]
        pred_hum = models['humidity'].predict(X_hum)

        X_rain = future_df[['temp', 'humidity', 'pressure', 'uv', 'wind_speed', 'hour', 'is_day']]
        pred_rain_prob = models['rain'].predict_proba(X_rain)[:, 1] * 100

        X_uv = future_df[['temp', 'humidity', 'pressure', 'rain', 'wind_speed', 'hour', 'is_day']]
        pred_uv = models['uv'].predict(X_uv)

        # --- แสดงผลตัวเลข (Forecast Metrics) ---
        st.subheader("🕒 พยากรณ์ล่วงหน้า (AI Forecast)")
        
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
        st.subheader("📊 เปรียบเทียบ: Zeus AI vs Standard API")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🌡️ อุณหภูมิ", "💧 ความชื้น", "☀️ UV Index", "🌧️ ฝน"])
        
        times = [current_dt + timedelta(hours=i) for i in range(24)]

        with tab1:
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(x=times, y=pred_temp, name='Zeus AI (Local)',
                                        line=dict(color='#FFD700', width=4)))
            fig_temp.add_trace(go.Scatter(x=times, y=hourly['temperature_2m'][:24], name='Standard API',
                                        line=dict(color='gray', dash='dot', width=2)))
            fig_temp.update_layout(template="plotly_dark", title="เปรียบเทียบอุณหภูมิ (Temperature)",
                                   yaxis_title="°C", hovermode="x unified")
            st.plotly_chart(fig_temp, use_container_width=True)

        with tab2:
            fig_hum = go.Figure()
            fig_hum.add_trace(go.Scatter(x=times, y=pred_hum, name='Zeus AI',
                                       line=dict(color='#00BFFF', width=4)))
            fig_hum.add_trace(go.Scatter(x=times, y=hourly['relative_humidity_2m'][:24], name='API Base',
                                       line=dict(color='gray', dash='dot', width=2)))
            fig_hum.update_layout(template="plotly_dark", title="เปรียบเทียบความชื้น (Humidity)",
                                  yaxis_title="%", hovermode="x unified")
            st.plotly_chart(fig_hum, use_container_width=True)

        with tab3:
            fig_uv = go.Figure()
            fig_uv.add_trace(go.Scatter(x=times, y=pred_uv, name='Zeus AI',
                                      line=dict(color='#FFA500', width=4)))
            fig_uv.add_trace(go.Scatter(x=times, y=hourly['uv_index'][:24], name='API Base',
                                      line=dict(color='gray', dash='dot', width=2)))
            fig_uv.update_layout(template="plotly_dark", title="เปรียบเทียบดัชนี UV",
                                 yaxis_title="Index", hovermode="x unified")
            st.plotly_chart(fig_uv, use_container_width=True)

        with tab4:
            fig_rain = make_subplots(specs=[[{"secondary_y": True}]])
            fig_rain.add_trace(go.Bar(x=times, y=pred_rain_prob, name='Zeus AI (Probability %)',
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

import random # ต้องใช้สุ่มคำตอบให้ดูไม่ซ้ำซาก

# def page_chatbot(data, models):
#     st.markdown("<h1 class='center-text'>💬 Ark Zeus Chat</h1>", unsafe_allow_html=True)
#     st.caption("🤖 ถามข้าเกี่ยวกับอนาคตที่ข้าคำนวณไว้ (ข้อมูลจาก Zeus AI Model)")
    
#     # 1. เตรียมข้อมูลเข้าโมเดล (เหมือนหน้า Oracle)
#     if models and 'hourly' in data:
#         hourly = data['hourly']
#         thai_tz = pytz.timezone('Asia/Bangkok')
#         current_dt = datetime.now(thai_tz)
#         current_h = current_dt.hour
        
#         next_24_hours = [(current_h + i) % 24 for i in range(24)]
#         is_day_list = [1 if 6 <= h <= 18 else 0 for h in next_24_hours]
        
#         # แก้ UV กลางคืน
#         uv_corrected = [val if is_day_list[i] == 1 else 0.0 for i, val in enumerate(hourly['uv_index'][:24])]

#         future_df = pd.DataFrame({
#             'temp': hourly['temperature_2m'][:24],
#             'humidity': hourly['relative_humidity_2m'][:24],
#             'pressure': hourly['surface_pressure'][:24],
#             'rain': hourly['rain'][:24],
#             'uv': uv_corrected,
#             'wind_speed': hourly['wind_speed_10m'][:24],
#             'hour': next_24_hours,
#             'is_day': is_day_list
#         })
        
#         # --- ให้ AI ทำนายล่วงหน้า 24 ชม. เก็บไว้ในตัวแปร ---
#         ai_temp = models['temp'].predict(future_df[['humidity', 'pressure', 'rain', 'uv', 'wind_speed', 'hour', 'is_day']])
#         ai_rain_prob = models['rain'].predict_proba(future_df[['temp', 'humidity', 'pressure', 'uv', 'wind_speed', 'hour', 'is_day']])[:, 1] * 100
#         ai_uv = models['uv'].predict(future_df[['temp', 'humidity', 'pressure', 'rain', 'wind_speed', 'hour', 'is_day']])
#     else:
#         st.error("⚠️ ข้ายังไม่พร้อม (โหลดโมเดลไม่สำเร็จ)")
#         return

#     # 2. จัดการ Chat History
#     if "messages" not in st.session_state:
#         st.session_state.messages = []
#         # ข้อความต้อนรับ
#         welcome_msg = "ข้าคือ Zeus... เจ้าอยากรู้อะไรเกี่ยวกับลมฟ้าอากาศ? (เช่น อีก 3 ชั่วโมงร้อนไหม, คืนนี้ฝนตกไหม)"
#         st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

#     # 3. แสดงข้อความเก่า
#     for msg in st.session_state.messages:
#         with st.chat_message(msg["role"]):
#             st.markdown(msg["content"])

#     # 4. รับคำถามจาก User
#     if prompt := st.chat_input("ถามข้ามาสิ..."):
#         st.session_state.messages.append({"role": "user", "content": prompt})
#         with st.chat_message("user"):
#             st.markdown(prompt)
            
#         # --- 🧠 สมองส่วนการตอบคำถาม (Intent Recognition) ---
#         response = ""
#         p = prompt.lower() # แปลงเป็นตัวเล็กเพื่อให้เช็คง่าย
        
#         # Scenario 1: ถามถึงอนาคตระยะสั้น (อีก ... ชั่วโมง)
#         hour_offset = 0
#         if "อีก" in p and "ชั่วโมง" in p:
#             # พยายามแกะเลขจากคำถาม (เช่น "อีก 3 ชั่วโมง")
#             try:
#                 words = p.split()
#                 for i, word in enumerate(words):
#                     if word == "อีก" and i+1 < len(words):
#                         if words[i+1].isdigit():
#                             hour_offset = int(words[i+1])
#                         break
#             except:
#                 hour_offset = 1 # ถ้าแกะไม่ออก ให้ default เป็น 1 ชม.
        
#         # Scenario 2: ถามถึงช่วงเวลา (คืนนี้, พรุ่งนี้)
#         elif "คืนนี้" in p:
#             hour_offset = 20 - current_h if current_h < 20 else 1 # เช็คตอน 2 ทุ่ม
#         elif "พรุ่งนี้" in p:
#             hour_offset = 24 # เช็ค 24 ชม. ข้างหน้า
#         elif "อากาศวันพรุ่งนี้" in p:
#             hour_offset = 24 # เช็ค 24 ชม. ข้างหน้า
#         # ตรวจสอบว่า hour_offset ไม่เกินข้อมูลที่เรามี (23 ชม.)
#         if hour_offset < 0: hour_offset = 1
#         if hour_offset > 23: hour_offset = 23
        
#         target_time = (current_dt + timedelta(hours=hour_offset)).strftime("%H:00")
        
#         # --- เริ่มสร้างคำตอบ ---
        
#         # A. ถามเรื่อง "ร้อน/อุณหภูมิ"
#         if any(x in p for x in ["ร้อน", "หนาว", "อุณหภูมิ", "กี่องศา"]):
#             temp_val = ai_temp[hour_offset]
#             if temp_val > 35:
#                 mood = "🔥 ข้าเห็นเปลวเพลิงแห่งความร้อนแรง!"
#                 advice = "ระวัง Heat Stroke ไว้ด้วยล่ะ"
#             elif temp_val < 22:
#                 mood = "❄️ ลมหนาวกำลังพัดผ่านมา..."
#                 advice = "หาเสื้อคลุมมาใส่ซะ"
#             else:
#                 mood = "☁️ อากาศกำลังสบาย"
#                 advice = "เหมาะแก่การออกมาเดินเล่น"
            
#             response = f"{mood} ณ เวลา {target_time} อุณหภูมิจะอยู่ที่ **{temp_val:.1f}°C**... {advice}"

#         # B. ถามเรื่อง "ฝน"
#         elif any(x in p for x in ["ฝน", "ร่ม", "ตกไหม", "เปียก"]):
#             rain_prob = ai_rain_prob[hour_offset]
#             if rain_prob > 60:
#                 response = f"⛈️ **แน่นอน!** เวลา {target_time} มีโอกาสฝนตกสูงถึง **{rain_prob:.0f}%** ข้าแนะนำให้เตรียมร่มไว้เลย"
#             elif rain_prob > 30:
#                 response = f"🌧️ **มีความเสี่ยง** เวลา {target_time} มีโอกาสฝนตก **{rain_prob:.0f}%** ท้องฟ้าอาจครึ้มๆ"
#             else:
#                 response = f"☀️ **วางใจได้** เวลา {target_time} โอกาสฝนตกเพียง **{rain_prob:.0f}%** ท้องฟ้าแจ่มใส"

#         # C. ถามเรื่อง "แดด/UV/กันแดด"
#         elif any(x in p for x in ["แดด", "uv", "กันแดด", "ดำ"]):
#             uv_val = ai_uv[hour_offset]
#             if uv_val > 8:
#                 response = f"☠️ **อันตรายมาก!** ดัชนี UV สูงปรี๊ดที่ **{uv_val:.1f}** เจ้าจะผิวไหม้ใน 15 นาทีถ้าไม่ทากันแดด!"
#             elif uv_val > 5:
#                 response = f"☀️ **แดดแรงนะ** ดัชนี UV อยู่ที่ **{uv_val:.1f}** ทากันแดดไว้หน่อยก็ดี"
#             else:
#                 response = f"😎 **สบายๆ** ดัชนี UV แค่ **{uv_val:.1f}** ไม่ต้องกังวลเรื่องผิวเสีย"

#         # D. คำถามทั่วไป / ทักทาย
#         elif "สวัสดี" in p or "หวัดดี" in p:
#             response = "สวัสดีมนุษย์... มีอะไรให้เทพเจ้าอย่างข้าช่วยเหลือไหม?"
#         elif "ขอบคุณ" in p:
#             response = "ด้วยความยินดี... ขอให้เจ้าปลอดภัย"
#         elif "ใคร" in p and "สร้าง" in p:
#             response = "ข้าถูกสร้างขึ้นโดยมนุษย์ผู้ชาญฉลาด (Project Zeus) เพื่อปกป้องพวกเจ้าจากภัยธรรมชาติ"
            
#         # E. ถ้าไม่เข้าเงื่อนไขอะไรเลย
#         else:
#             response = "ข้าไม่เข้าใจคำถามของเจ้า... ลองถามเจาะจงหน่อยได้ไหม? เช่น 'อีก 2 ชั่วโมงร้อนไหม' หรือ 'เย็นนี้ฝนตกไหม ,หรือ อากาศวันพรุ่งนี้'"

#         # ส่งคำตอบกลับ
#         st.session_state.messages.append({"role": "assistant", "content": response})
#         with st.chat_message("assistant"):
#             st.markdown(response)

import re # ใช้สำหรับจับคำ keyword แบบฉลาดๆ

def page_chatbot(data, models):
    st.markdown("<h1 class='center-text'>💬 Ark Zeus Chat (Intel Mode)</h1>", unsafe_allow_html=True)
    st.caption("🤖 ถามข้าได้ลึกซึ้งขึ้น เช่น 'บ่ายนี้ตากผ้าได้ไหม', 'เย็นนี้วิ่งได้รึเปล่า', 'ทำไมฝนถึงจะตก'")

    # --- 1. เตรียมข้อมูลเข้าโมเดล (เหมือนหน้า Oracle) ---
    if models and 'hourly' in data:
        hourly = data['hourly']
        thai_tz = pytz.timezone('Asia/Bangkok')
        current_dt = datetime.now(thai_tz)
        current_h = current_dt.hour
        
        # เตรียมข้อมูลล่วงหน้า 24 ชม.
        next_24_hours = [(current_h + i) % 24 for i in range(24)]
        is_day_list = [1 if 6 <= h <= 18 else 0 for h in next_24_hours]
        
        # แก้ UV กลางคืน
        uv_corrected = [val if is_day_list[i] == 1 else 0.0 for i, val in enumerate(hourly['uv_index'][:24])]

        future_df = pd.DataFrame({
            'temp': hourly['temperature_2m'][:24],
            'humidity': hourly['relative_humidity_2m'][:24],
            'pressure': hourly['surface_pressure'][:24],
            'rain': hourly['rain'][:24],
            'uv': uv_corrected,
            'wind_speed': hourly['wind_speed_10m'][:24],
            'hour': next_24_hours,
            'is_day': is_day_list
        })
        
        # ให้ AI ทำนายรวดเดียว 24 ชม.
        ai_temp = models['temp'].predict(future_df[['humidity', 'pressure', 'rain', 'uv', 'wind_speed', 'hour', 'is_day']])
        ai_hum = models['humidity'].predict(future_df[['temp', 'pressure', 'rain', 'uv', 'wind_speed', 'hour', 'is_day']])
        ai_rain_prob = models['rain'].predict_proba(future_df[['temp', 'humidity', 'pressure', 'uv', 'wind_speed', 'hour', 'is_day']])[:, 1] * 100
        ai_uv = models['uv'].predict(future_df[['temp', 'humidity', 'pressure', 'rain', 'wind_speed', 'hour', 'is_day']])
    else:
        st.error("⚠️ ข้ายังไม่พร้อม (โหลดโมเดลไม่สำเร็จ)")
        return

    # --- 2. Chat Logic ---
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role": "assistant", "content": "ข้าคือ Zeus ผู้หยั่งรู้ฟ้าดิน... เจ้าอยากวางแผนชีวิตเรื่องใด? (ตากผ้า, ออกกำลังกาย, เดินทาง)"})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("พิมพ์คำถามของเจ้าที่นี่..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # --- 🧠 BRAIN LEVEL 2: Advanced Processing ---
        p = prompt.lower()
        response = ""
        
        # [A] หาช่วงเวลาเป้าหมาย (Target Time Extraction)
        # Default = อีก 1 ชม.
        hour_offset = 1 
        
        # Keyword ช่วงเวลา
        if "เช้า" in p: hour_offset = (8 - current_h) if current_h < 8 else (32 - current_h) # 8 โมงเช้า
        elif "เที่ยง" in p: hour_offset = (12 - current_h) if current_h < 12 else (36 - current_h)
        elif "บ่าย" in p: hour_offset = (14 - current_h) if current_h < 14 else (38 - current_h) # บ่าย 2
        elif "เย็น" in p: hour_offset = (18 - current_h) if current_h < 18 else (42 - current_h) # 6 โมงเย็น
        elif "ค่ำ" in p or "ดึก" in p or "คืนนี้" in p: hour_offset = (21 - current_h) if current_h < 21 else (45 - current_h) # 3 ทุ่ม
        
        # Regex หาตัวเลข (เช่น "อีก 3 ชม", "อีก 5 ชั่วโมง")
        match = re.search(r"อีก\s*(\d+)", p)
        if match:
            hour_offset = int(match.group(1))

        # Clamp ค่าให้อยู่ในช่วง 0-23 (เพราะเรามีข้อมูลแค่ 24 ชม.)
        if hour_offset >= 24:
            response = "⚠️ ญาณหยั่งรู้ของข้าเห็นได้ไกลสุดเพียง 24 ชั่วโมงเท่านั้น... ข้าจะตอบคำถามของเจ้าสำหรับ **พรุ่งนี้เวลานี้** แทนนะ"
            hour_offset = 23
        elif hour_offset < 0:
            hour_offset = 1 # กันพลาด
            
        target_time_str = (current_dt + timedelta(hours=hour_offset)).strftime("%H:00")
        
        # ดึงค่าพยากรณ์ ณ เวลานั้น
        pred_t = ai_temp[hour_offset]
        pred_h = ai_hum[hour_offset]
        pred_r_prob = ai_rain_prob[hour_offset]
        pred_uv = ai_uv[hour_offset]

        # [B] ตอบคำถามตามเจตนา (Intent Classification)
        
        # 1. ถามเรื่อง "กิจกรรม" (Activity Advice)
        if any(x in p for x in ["ตากผ้า", "ซักผ้า"]):
            if pred_r_prob < 20 and pred_uv > 3:
                response = f"👕 **ตากได้เลย!** เวลา {target_time_str} แดดดี (UV {pred_uv:.1f}) และโอกาสฝนต่ำมาก ({pred_r_prob:.0f}%) ผ้าแห้งไวแน่นอน"
            elif pred_r_prob > 50:
                response = f"👕❌ **อย่าเสี่ยง!** เวลา {target_time_str} มีโอกาสฝนสูงถึง {pred_r_prob:.0f}% ผ้าเจ้าจะเปียกปอน"
            else:
                response = f"👕 **พอไหว** แต่ต้องคอยดูเมฆหน่อยนะ (โอกาสฝน {pred_r_prob:.0f}%)"

        elif any(x in p for x in ["วิ่ง", "ออกกำลังกาย", "จอกกิ้ง"]):
            if pred_r_prob > 40:
                response = f"🏃❌ **พักก่อนดีกว่า** ฝนน่าจะตก (โอกาส {pred_r_prob:.0f}%) เดี๋ยวจะไม่สบาย"
            elif pred_t > 33:
                response = f"🏃⚠️ **ร้อนไปนะ** อุณหภูมิ {pred_t:.1f}°C เสี่ยง Heat Stroke รอเย็นกว่านี้เถอะ"
            else:
                response = f"🏃✅ **ลุยเลย!** เวลา {target_time_str} อากาศกำลังดี ({pred_t:.1f}°C) เหมาะแก่การเผาผลาญไขมัน"
                
        elif any(x in p for x in ["ล้างรถ"]):
            if any(r > 40 for r in ai_rain_prob[hour_offset:hour_offset+6]): # เช็คยาวๆ 6 ชม.
                response = f"🚗❌ **อย่าเพิ่งล้าง** ข้าเห็นเมฆฝนก่อตัวในอีกไม่กี่ชั่วโมงข้างหน้า ล้างไปก็เลอะอยู่ดี"
            else:
                response = f"🚗✨ **ล้างได้เลย** ฟ้าโปร่งยาวๆ รถเจ้าจะเงางามแน่นอน"

        # 2. ถาม "ทำไม" (Explainability)
        elif "ทำไม" in p or "เพราะ" in p:
            if "ฝน" in p:
                response = f"⛈️ ที่ข้าทำนายว่าฝนอาจตก เพราะข้าเห็น **ความชื้นสะสมสูงถึง {pred_h:.1f}%** ผสมกับความกดอากาศที่เปลี่ยนแปลง"
            elif "ร้อน" in p:
                response = f"🔥 ที่อากาศร้อน เพราะ **ค่า UV สูงถึง {pred_uv:.1f}** และความชื้นต่ำ ทำให้ความร้อนสะสมตัวได้ดี"
            else:
                response = "มันเป็นกลไกของธรรมชาติ ที่ข้าคำนวณจากสถิติและความน่าจะเป็นของข้อมูลกว่าหมื่นรายการ"

        # 3. ถามทั่วไป (General)
        elif "ฝน" in p:
            if pred_r_prob > 50:
                response = f"🌧️ เวลา {target_time_str} มีโอกาสฝนตก **{pred_r_prob:.0f}%** เตรียมร่มไว้เถิด"
            else:
                response = f"☁️ เวลา {target_time_str} ฝนไม่น่าตก (โอกาสเพียง {pred_r_prob:.0f}%)"
                
        elif "ร้อน" in p or "อุณหภูมิ" in p:
            response = f"🌡️ เวลา {target_time_str} อุณหภูมิประมาณ **{pred_t:.1f}°C** (ความชื้น {pred_h:.0f}%)"
            
        else:
            # คำถามทักทาย / ไม่เข้าใจ
            greetings = ["ข้าพร้อมรับใช้", "ถามเรื่องอากาศเถิด ข้าถนัดที่สุด", "วันนี้เจ้าดูสดใสนะ"]
            response = f"{random.choice(greetings)}... ลองถามว่า 'เย็นนี้ตากผ้าได้ไหม' หรือ 'อีก 3 ชม. ร้อนไหม' ดูสิ"

        # ส่งคำตอบ
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# ==========================================
# 5. MAIN APP CONTROLLER
# ==========================================

# --- SIDEBAR SETTINGS ---

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3062/3062634.png", width=80) 
st.sidebar.title("ZEUS MENU")
page = st.sidebar.radio("เลือกเมนู", ["Dashboard", "The Oracle", "Ark Zeus Chat"])

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
        if page == "Dashboard":
            page_dashboard(data)
        elif page == "The Oracle":
            page_oracle(data, models)
        elif page == "Ark Zeus Chat":
            page_chatbot(data,models)
else:
    st.error("Connection Error: ไม่สามารถดึงข้อมูลจาก Open-Meteo ได้")