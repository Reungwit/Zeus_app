import streamlit as st
import pandas as pd
import numpy as np
import joblib
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
    .main-content { margin-top: 80px; }
    
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
        text-align: center;
        margin: auto;
    }
    div[data-testid="stMetricLabel"] { justify-content: center; }
    div[data-testid="stMetricValue"] { justify-content: center; color: #FFD700; }
    
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
@st.cache_resource
def load_resources():
    try:
        model = joblib.load('zeus_oracle_model.pkl') 
    except:
        model = None
    return model

model = load_resources()

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

def calculate_burn_rate(uv_index):
    if uv_index <= 2: return "Low", "ผิวไม่ไหม้ง่ายๆ (60+ นาที)"
    elif uv_index <= 5: return "Moderate", "ได้ประมาณ 45 นาที"
    elif uv_index <= 7: return "High", "ระวัง! (30 นาที)"
    elif uv_index <= 10: return "Very High", "อันตราย! (15-25 นาที)"
    else: return "Extreme", "🔥 ไหม้ใน < 10 นาที"

def calculate_heat_index(temp, humidity):
    hi = temp + 0.33 * (humidity/100 * 6.105 * np.exp(17.27 * temp / (237.7 + temp))) - 4
    if hi < 27: return hi, "🏃 สบาย: วิ่งจอกกิ้งได้", "green"
    elif hi < 32: return hi, "⚠️ เริ่มร้อน: จิบน้ำบ่อยๆ", "orange"
    elif hi < 41: return hi, "🏠 ร้อนชื้น: อยู่ในร่มเถอะ", "red"
    else: return hi, "☠️ อันตราย: Heat Stroke!", "darkred"

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
    st.markdown("<h1 class='center-text'>👁️ Zeus Eye (Dashboard)</h1>", unsafe_allow_html=True)
    current = data['current']
    
    # Metrics Grid
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("🌡️ Temp", f"{current['temperature_2m']} °C")
    with c2: st.metric("💧 Humidity", f"{current['relative_humidity_2m']} %")
    with c3: st.metric("☁️ Status", "ฝนตก" if current['rain']>0 else "ปกติ")
    with c4: st.metric("⬇️ Pressure", f"{current['surface_pressure']} hPa")
    
    st.divider()
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("⛈️ Zeus's Mood")
        msg, icon, alert = check_zeus_mood(current['surface_pressure'], current['relative_humidity_2m'], current['rain'])
        st.markdown(f"<h1 style='text-align:center; font-size:60px;'>{icon}</h1>", unsafe_allow_html=True)
        if alert: st.error(msg)
        else: st.info(msg)
        
    with col_r:
        st.subheader("🛡️ Apollo's Shield")
        uv_now = data['hourly']['uv_index'][datetime.now().hour]
        burn, adv = calculate_burn_rate(uv_now)
        st.metric("☀️ UV Index", f"{uv_now}")
        st.warning(f"{burn}: {adv}")

def page_oracle(data, model):
    st.markdown("<h1 class='center-text'>🔮 The Oracle (คำทำนาย)</h1>", unsafe_allow_html=True)
    
    if model:
        hourly = data['hourly']
        current_h = datetime.now().hour
        next_24_hours = [(current_h + i) % 24 for i in range(24)]
        
        future_data = {
            'humidity': hourly['relative_humidity_2m'][:24],
            'pressure': hourly['surface_pressure'][:24],
            'rain': hourly['rain'][:24],
            'uv': hourly['uv_index'][:24],
            'wind_speed': hourly['wind_speed_10m'][:24], 
            'hour': next_24_hours,
            'is_day': [1 if 6 <= h <= 18 else 0 for h in next_24_hours]
        }
        X_pred = pd.DataFrame(future_data)
        
        try:
            feature_order = ['humidity', 'pressure', 'rain', 'uv', 'wind_speed', 'hour', 'is_day']
            X_input = X_pred[feature_order] 
            y_pred = model.predict(X_input)
            
            next_temp = y_pred[1]
            curr_temp = data['current']['temperature_2m']
            diff = next_temp - curr_temp
            
            msg = "😐 อุณหภูมิคงที่"
            if diff > 0.5: msg = f"🔥 ร้อนขึ้น (+{diff:.1f}°C)"
            elif diff < -0.5: msg = f"❄️ เย็นลง ({diff:.1f}°C)"
            
            st.success(f"🤖 AI Prediction: อีก 1 ชม. {msg}")
            
            fig = go.Figure()
            times = [datetime.now() + timedelta(hours=i) for i in range(24)]
            fig.add_trace(go.Scatter(x=times, y=y_pred, name='Zeus AI', line=dict(color='#FFD700', width=3)))
            fig.add_trace(go.Scatter(x=times, y=hourly['temperature_2m'][:24], name='API Base', line=dict(color='gray', dash='dash')))
            fig.update_layout(template="plotly_dark", title="พยากรณ์อุณหภูมิ 24 ชม.", paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("⚠️ ไม่พบไฟล์โมเดล AI")

def page_chatbot(data):
    st.markdown("<h1 class='center-text'>💬 Ark Zeus Chat</h1>", unsafe_allow_html=True)
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("ถามข้ามาสิ..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        response = "ข้าไม่เข้าใจ..."
        if "ฝน" in prompt and "พรุ่งนี้" in prompt:
            rain_tmr = data['hourly']['rain'][24:48]
            if sum(rain_tmr) > 0:
                response = f"⛈️ พรุ่งนี้มีฝนรวม {sum(rain_tmr):.1f} มม. เตรียมร่มไว้เถิด"
            else:
                response = "☀️ พรุ่งนี้ฟ้าโปร่ง ข้าไม่เห็นฝน"
        elif "ร้อน" in prompt:
            t = data['current']['temperature_2m']
            response = f"ตอนนี้ {t}°C ร้อนหรือไม่เจ้าตัดสินใจเอง"
            
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# ==========================================
# 5. MAIN APP CONTROLLER
# ==========================================

# --- SIDEBAR SETTINGS ---
st.sidebar.markdown("<br><br>", unsafe_allow_html=True) # ดันเนื้อหา Sidebar ลงมาหน่อยจะได้ไม่ชนปุ่มปิด
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3062/3062634.png", width=80) 
st.sidebar.title("⚡ ZEUS MENU")
page = st.sidebar.radio("เลือกเมนู", ["Dashboard", "The Oracle", "Ark Zeus Chat"])

st.sidebar.divider()
st.sidebar.caption("📍 Location: Prachin Buri")
st.sidebar.caption("Model: Random Forest")

# Fetch Data
data = get_open_meteo_data()

if data:
    # Grid Layout จัดกลาง
    left_co, cent_co, last_co = st.columns([1, 8, 1])
    
    with cent_co:
        if page == "Dashboard":
            page_dashboard(data)
        elif page == "The Oracle":
            page_oracle(data, model)
        elif page == "Ark Zeus Chat":
            page_chatbot(data)
else:
    st.error("Connection Error: ไม่สามารถดึงข้อมูลจาก Open-Meteo ได้")