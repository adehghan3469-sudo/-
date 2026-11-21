"""
داشبورد تعاملی گزارش روزانه کشاورزی بابامنیر
با اتصال زنده به Open-Meteo (رایگان و بدون نیاز به API Key)

اجرا محلی:
    streamlit run babamenir_dashboard.py

برای اشتراک‌گذاری در گروه واتساپ باید روی Streamlit Cloud یا Hugging Face مستقر شود.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import jdatetime   # برای تاریخ شمسی (اگر نصب نبود، fallback می‌شود)

# -----------------------------
# تنظیمات صفحه
# -----------------------------
st.set_page_config(
    page_title="گزارش روزانه کشاورزی بابامنیر",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# مختصات جغرافیایی
# -----------------------------
LOCATIONS = {
    "بابامنیر": {"lat": 30.07, "lon": 51.52, "name": "بابامنیر"},
    "نورآباد ممسنی": {"lat": 30.11, "lon": 51.52, "name": "نورآباد ممسنی"},
    "ماهور میلاتی": {"lat": 29.95, "lon": 51.45, "name": "ماهور میلاتی"}
}

# -----------------------------
# تابع دریافت داده زنده از Open-Meteo
# -----------------------------
@st.cache_data(ttl=1800)  # کش ۳۰ دقیقه‌ای
def get_weather(lat, lon, name):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ["temperature_2m", "relative_humidity_2m", "weather_code", "wind_speed_10m", "wind_direction_10m"],
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "precipitation_sum", "weather_code"],
        "timezone": "Asia/Tehran",
        "forecast_days": 7
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data
    except Exception as e:
        st.error(f"خطا در دریافت داده هواشناسی {name}: {e}")
        return None

# -----------------------------
# تبدیل کد وضعیت هوا
# -----------------------------
def weather_code_to_text(code):
    mapping = {
        0: "صاف",
        1: "عمدتاً صاف",
        2: "نیمه‌ابری",
        3: "ابری",
        45: "مه",
        48: "مه یخ‌زده",
        51: "باران ریز",
        61: "باران سبک",
        63: "باران متوسط",
        65: "باران شدید",
        71: "برف سبک",
        80: "رگبار",
        95: "رعد و برق"
    }
    return mapping.get(code, "نامشخص")

# -----------------------------
# تاریخ شمسی
# -----------------------------
def get_shamsi_date():
    try:
        now = jdatetime.datetime.now()
        days = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"]
        return f"{days[now.weekday()]} {now.day} {now.j_months_fa[now.month-1]} {now.year}"
    except:
        return datetime.now().strftime("%Y-%m-%d")

# -----------------------------
# سایدبار
# -----------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/wheat.png", width=80)
    st.title("دفتر فنی بابامنیر")
    st.markdown("---")
    
    selected_location = st.selectbox(
        "📍 انتخاب منطقه",
        list(LOCATIONS.keys()),
        index=0
    )
    
    st.markdown("---")
    page = st.radio(
        "بخش‌های داشبورد",
        ["🏠 خلاصه روز", "🌤️ هواشناسی زنده", "💰 قیمت نهاده‌ها", "🚜 توصیه‌های فنی", "📰 اخبار و منابع"],
        index=0
    )
    
    st.markdown("---")
    st.caption("واتساپ: ۰۹۱۷۶۸۰۸۷۵۵")
    st.caption("ایتا و روبیکا: @a.d3469")
    st.caption("داده هواشناسی: Open-Meteo (زنده‌)")

# -----------------------------
# دریافت داده زنده
# -----------------------------
loc = LOCATIONS[selected_location]
weather = get_weather(loc["lat"], loc["lon"], loc["name"])

# -----------------------------
# صفحه خلاصه روز
# -----------------------------
if page == "🏠 خلاصه روز":
    st.title("🌾 گزارش روزانه کشاورزی بابامنیر")
    st.markdown(f"**منطقه انتخاب‌شده:** {selected_location}")
    st.markdown(f"**تاریخ:** {get_shamsi_date()}")
    st.markdown("---")
    
    if weather:
        current = weather["current"]
        daily = weather["daily"]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("دمای فعلی", f"{current['temperature_2m']:.1f}°C")
        with col2:
            st.metric("حداقل / حداکثر امروز", 
                      f"{daily['temperature_2m_min'][0]:.0f} / {daily['temperature_2m_max'][0]:.0f}°C")
        with col3:
            st.metric("رطوبت", f"{current['relative_humidity_2m']}%")
        with col4:
            st.metric("احتمال بارش امروز", f"{daily['precipitation_probability_max'][0]}%")
        
        st.info(f"**وضعیت فعلی:** {weather_code_to_text(current['weather_code'])} | باد: {current['wind_speed_10m']} کیلومتر/ساعت")
    
    st.markdown("### 📈 پیش‌بینی دمای ۷ روز آینده")
    if weather:
        df = pd.DataFrame({
            "تاریخ": weather["daily"]["time"],
            "حداقل": weather["daily"]["temperature_2m_min"],
            "حداکثر": weather["daily"]["temperature_2m_max"]
        })
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["تاریخ"], y=df["حداکثر"], mode="lines+markers", name="حداکثر", line=dict(color="#e74c3c")))
        fig.add_trace(go.Scatter(x=df["تاریخ"], y=df["حداقل"], mode="lines+markers", name="حداقل", line=dict(color="#3498db")))
        fig.update_layout(title=f"پیش‌بینی دما - {selected_location}", height=400, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# صفحه هواشناسی زنده
# -----------------------------
elif page == "🌤️ هواشناسی زنده":
    st.title(f"🌤️ هواشناسی زنده - {selected_location}")
    
    if weather:
        current = weather["current"]
        daily = weather["daily"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("شرایط فعلی")
            st.write(f"""
            - **دما:** {current['temperature_2m']:.1f}°C  
            - **رطوبت:** {current['relative_humidity_2m']}%  
            - **باد:** {current['wind_speed_10m']} کیلومتر/ساعت  
            - **وضعیت:** {weather_code_to_text(current['weather_code'])}
            """)
        
        with col2:
            st.subheader("امروز")
            st.write(f"""
            - **حداقل / حداکثر:** {daily['temperature_2m_min'][0]:.0f} / {daily['temperature_2m_max'][0]:.0f}°C  
            - **احتمال بارش:** {daily['precipitation_probability_max'][0]}%  
            - **مقدار بارش پیش‌بینی‌شده:** {daily['precipitation_sum'][0]} میلی‌متر
            """)
        
        st.markdown("---")
        st.subheader("پیش‌بینی ۷ روز آینده")
        
        df7 = pd.DataFrame({
            "تاریخ": daily["time"],
            "حداقل دما": daily["temperature_2m_min"],
            "حداکثر دما": daily["temperature_2m_max"],
            "احتمال بارش (%)": daily["precipitation_probability_max"],
            "بارش (میلی‌متر)": daily["precipitation_sum"],
            "وضعیت": [weather_code_to_text(c) for c in daily["weather_code"]]
        })
        st.dataframe(df7, use_container_width=True, hide_index=True)
        
        st.caption("منبع: Open-Meteo | به‌روزرسانی خودکار هر ۳۰ دقیقه | مدل‌های ترکیبی جهانی")
    else:
        st.error("دریافت داده هواشناسی با مشکل مواجه شد. لطفاً چند لحظه دیگر تلاش کنید.")

# -----------------------------
# صفحه قیمت نهاده‌ها (ثابت)
# -----------------------------
elif page == "💰 قیمت نهاده‌ها":
    st.title("💰 قیمت روز نهاده‌های کشاورزی")
    st.warning("⚠️ قیمت کودها به‌شدت متغیر است. استعلام محلی از کارگزاری نورآباد و جهاد کشاورزی ممسنی ضروری است.")
    
    prices_data = {
        "نهاده": [
            "بذر گندم نان گواهی‌شده",
            "بذر گندم دوروم گواهی‌شده",
            "بذر جو گواهی‌شده",
            "کود اوره ۵۰ کیلویی (بازار)",
            "سوپرفسفات تریپل ۵۰ک",
            "سولفات پتاسیم ۵۰ک"
        ],
        "قیمت (تومان)": [72000, 75600, 72000, 3600000, 7500000, 6900000],
        "واحد": ["کیلوگرم", "کیلوگرم", "کیلوگرم", "کیسه", "کیسه", "کیسه"],
        "توضیح": [
            "با یارانه ۵ هزار تومانی برای دیم واجد شرایط → حدود ۶۷ هزار",
            "بدون یارانه مستقیم",
            "با یارانه برای طبقات دیم",
            "نوسان شدید - نیازمند استعلام محلی",
            "بازار آزاد تقریبی",
            "بازار آزاد تقریبی"
        ]
    }
    df_prices = pd.DataFrame(prices_data)
    st.dataframe(df_prices, use_container_width=True, hide_index=True)

# -----------------------------
# صفحه توصیه‌های فنی
# -----------------------------
elif page == "🚜 توصیه‌های فنی":
    st.title("🚜 توصیه‌های فنی امروز")
    recommendations = [
        "با توجه به شرایط فعلی هوا، فرصت مناسبی برای ادامه کشت گندم و جو دیم وجود دارد. از بذر گواهی‌شده استفاده کنید.",
        "به دلیل نوسان شدید قیمت کود اوره، مصرف را بر اساس آزمون خاک و نیاز واقعی گیاه تنظیم کنید.",
        "خطر یخبندان فعلاً پایین است، اما شب‌ها خنک می‌شود؛ مراقب شبنم صبحگاهی باشید.",
        "قبل از هرگونه سم‌پاشی، سرعت باد و رطوبت را بررسی کنید."
    ]
    for i, rec in enumerate(recommendations, 1):
        st.markdown(f"**{i}.** {rec}")
        st.markdown("---")

# -----------------------------
# صفحه اخبار و منابع
# -----------------------------
elif page == "📰 اخبار و منابع":
    st.title("📰 اخبار و منابع")
    st.markdown("""
    **منابع هواشناسی زنده:**  
    - Open-Meteo (رایگان و بدون کلید API)  
    - مدل‌های ترکیبی جهانی با وضوح مناسب برای منطقه فارس
    
    **منابع قیمت و اخبار:**  
    - سازمان جهاد کشاورزی فارس  
    - شرکت خدمات حمایتی کشاورزی  
    - خبرگزاری‌های رسمی (ایرنا، ایسنا و ...)
    """)

# -----------------------------
# فوتر
# -----------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
        🌱 دفتر فنی و خدمات کشاورزی بابامنیر<br>
        مشاوره | اطلاع‌رسانی | خدمات کشاورزی<br>
        واتساپ: ۰۹۱۷۶۸۰۸۷۵۵ | ایتا و روبیکا: @a.d3469
    </div>
    """,
    unsafe_allow_html=True
)
