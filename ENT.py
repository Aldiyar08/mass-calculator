import streamlit as st
import sqlite3
import os
import hashlib
import base64
from datetime import date
import google.generativeai as genai
from foods import FOOD_DATABASE

# 1. Настройки страницы
st.set_page_config(page_title="Масса-Комбайн ИИ", page_icon="🤖", layout="wide")

# --- ИНИЦИАЛИЗАЦИЯ НАСТОЯЩЕЙ БАЗЫ ДАННЫХ SQLITE ---
def init_db():
    conn = sqlite3.connect("cyber_muscle.db")
    cursor = conn.cursor()
    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    # Таблица истории КБЖУ по дням
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            username TEXT,
            date TEXT,
            kcal INTEGER,
            target_kcal INTEGER,
            protein REAL,
            target_protein INTEGER,
            water INTEGER,
            target_water INTEGER,
            PRIMARY KEY (username, date)
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- ДЕКОДИРОВАНИЕ API КЛЮЧА ИИ ---
def get_decrypted_key():
    # Замени значение внутри кавычек на свою строку из base64encode.org!
    ENCRYPTED_KEY = "QUl6YVN5QVEuQWI4Uk42TEtCY2RCQTBJUXNLRmVLc0xTLTdBT09ITm5vMWpVWU1qS3ZQc1R0SURabUE" 
    
    if ENCRYPTED_KEY == "QUl6YVN5QVEuQWI4Uk42TEtCY2RCQTBJUXNLRmVLc0xTLTdBT09ITm5vMWpVWU1qS3ZQc1R0SURabUE":
        return None
    try:
        decoded_bytes = base64.b64decode(ENCRYPTED_KEY)
        return decoded_bytes.decode("utf-8").strip()
    except:
        return None

# Настройка ИИ
REAL_API_KEY = get_decrypted_key()
if REAL_API_KEY and REAL_API_KEY.startswith("AIzaSy"):
    os.environ["GEMINI_API_KEY"] = REAL_API_KEY
    genai.configure(api_key=REAL_API_KEY)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Инициализация переменных сессии Streamlit
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "meal_bag" not in st.session_state:
    st.session_state.meal_bag = []
if "water_intake" not in st.session_state:
    st.session_state.water_intake = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- ЭКРАН АВТОРИЗАЦИИ / РЕГИСТРАЦИИ ---
if not st.session_state.logged_in:
    st.title("💪 Добро пожаловать в Масса-Комбайн ИИ!")
    st.write("Данные теперь сохраняются в базу SQL. Авторизуйся для входа:")
    
    auth_tab, reg_tab = st.tabs(["🔑 Вход", "📝 Регистрация"])
    
    with auth_tab:
        login_user = st.text_input("Логин:", key="login_u")
        login_pass = st.text_input("Пароль:", type="password", key="login_p")
        if st.button("Войти 🚀", use_container_width=True):
            conn = sqlite3.connect("cyber_muscle.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (login_user, hash_password(login_pass)))
            user = cursor.fetchone()
            conn.close()
            
            if user:
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.success(f"Рады видеть тебя, {login_user}!")
                st.rerun()
            else:
                st.error("Неверный логин или пароль.")
                
    with reg_tab:
        reg_user = st.text_input("Уникальный логин:", key="reg_u")
        reg_pass = st.text_input("Пароль:", type="password", key="reg_p")
        if st.button("Создать аккаунт 🎉", use_container_width=True):
            if reg_user and reg_pass:
                try:
                    conn = sqlite3.connect("cyber_muscle.db")
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (reg_user, hash_password(reg_pass)))
                    conn.commit()
                    conn.close()
                    st.session_state.logged_in = True
                    st.session_state.username = reg_user
                    st.success("Аккаунт успешно создан в SQL базе!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Этот логин уже занят!")
            else:
                st.warning("Заполни все поля!")
    st.stop()

# --- ГЛАВНЫЙ ИНТЕРФЕЙС ---
current_user = st.session_state.username

st.sidebar.write(f"👤 Профиль: **{current_user}** [SQL DB]")
if st.sidebar.button("Выйти 🚪", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.meal_bag = []
    st.session_state.water_intake = 0
    st.session_state.chat_history = []
    st.rerun()

st.title(f"🏋️‍♂️ Масса-Комбайн ИИ")

# Параметры тела
st.sidebar.header("🎯 Параметры")
user_gender = st.sidebar.radio("Пол:", ["Мужской", "Женский"])
user_age = st.sidebar.number_input("Возраст:", min_value=12, max_value=80, value=18)
user_height = st.sidebar.number_input("Рост (см):", min_value=120, max_value=220, value=188)
user_weight = st.sidebar.number_input("Вес (кг):", min_value=35, max_value=180, value=71)

# Формула Миффлина
if user_gender == "Мужской":
    bmr = (10 * user_weight) + (6.25 * user_height) - (5 * user_age) + 5
else:
    bmr = (10 * user_weight) + (6.25 * user_height) - (5 * user_age) - 161

target_kcal = (bmr * 1.375) + 500
target_p = user_weight * 2.0
target_f = user_weight * 1.0
target_c = (target_kcal - (target_p * 4) - (target_f * 9)) / 4
target_water = round((user_weight * 35) / 1000, 1)

st.sidebar.markdown(f"""
### 📊 Цель на массу:
* 🔥 Калории: **{round(target_kcal)} ккал**
* 🍗 Белки: **{round(target_p)} г**
* 💧 Вода: **{target_water} л**
""")

tab_diary, tab_history, tab_ai = st.tabs(["📝 Дневник питания", "📈 Моя SQL История", "🤖 ИИ-Тренер"])

# ВКЛАДКА 1: ДНЕВНИК
with tab_diary:
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("🔍 Добавить еду")
        meal_type = st.radio("Приём пищи:", ["Завтрак 🍳", "Обед 🍲", "Ужин 🥩", "Перекус 🍏"], horizontal=True)
        selected_product = st.selectbox("Выбор продукта:", options=list(FOOD_DATABASE.keys()), index=None)
        
        if selected_product:
            nutr = FOOD_DATABASE[selected_product]
            amount = st.number_input(f"Укажи вес ({nutr['unit']}):", min_value=1, value=150, step=10)
            
            if st.button("Добавить еду ➕", use_container_width=True):
                ratio = amount / 100.0
                st.session_state.meal_bag.append({
                    "meal_type": meal_type, "name": selected_product, "amount": amount, "unit": nutr["unit"],
                    "kcal": nutr["калории"] * ratio, "p": nutr["белки"] * ratio, "f": nutr["жиры"] * ratio, "c": nutr["углеводы"] * ratio
                })
                st.rerun()
                
        st.markdown("---")
        st.subheader("💧 Вода")
        st.write(f"Выпито: **{st.session_state.water_intake} мл**")
        if st.button("🥛 +250 мл", use_container_width=True):
            st.session_state.water_intake += 250
            st.rerun()

    with col_right:
        st.subheader("📋 Сегодняшний рацион")
        total_kcal = total_p = total_f = total_c = 0
        
        for cat in ["Завтрак 🍳", "Обед 🍲", "Ужин 🥩", "Перекус 🍏"]:
            cat_items = [i for i in st.session_state.meal_bag if i["meal_type"] == cat]
            if cat_items:
                st.markdown(f"**{cat}**")
                for item in cat_items:
                    total_kcal += item["kcal"]
                    total_p += item["p"]
                    total_f += item["f"]
                    total_c += item["c"]
                    st.write(f"▪️ {item['name']} ({item['amount']}{item['unit']}) — {round(item['kcal'])} ккал")

        if st.session_state.meal_bag or st.session_state.water_intake > 0:
            st.markdown("---")
            st.write(f"🔥 Всего: {round(total_kcal)} / {round(target_kcal)} ккал")
            st.progress(min(max(total_kcal / target_kcal, 0.0), 1.0))
            
            if st.button("💾 ФИКСИРОВАТЬ ДЕНЬ В SQL БАЗУ", use_container_width=True, type="primary"):
                conn = sqlite3.connect("cyber_muscle.db")
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO history (username, date, kcal, target_kcal, protein, target_protein, water, target_water)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (current_user, str(date.today()), round(total_kcal), round(target_kcal), round(total_p, 1), round(target_p), st.session_state.water_intake, round(target_water * 1000)))
                conn.commit()
                conn.close()
                st.balloons()
                st.success("Данные надежно записаны в таблицы базы данных!")
                
            if st.button("Очистить дневник 🗑️", use_container_width=True):
                st.session_state.meal_bag = []
                st.session_state.water_intake = 0
                st.rerun()

# ВКЛАДКА 2: ИСТОРИЯ (ИЗ SQL)
with tab_history:
    st.subheader("📊 Твои архивные записи из SQLite")
    conn = sqlite3.connect("cyber_muscle.db")
    cursor = conn.cursor()
    cursor.execute("SELECT date, kcal, target_kcal, protein, water FROM history WHERE username = ? ORDER BY date DESC", (current_user,))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        for row in rows:
            st.write(f"📅 **{row[0]}** | Съедено: **{row[1]}** / {row[2]} ккал | Белок: {row[3]}г | Вода: {row[4]}мл")
    else:
        st.info("В SQL базе пока нет записей. Сохрани текущий день на вкладке дневника!")

# ВКЛАДКА 3: ИИ-ТРЕНЕР
with tab_ai:
    st.subheader("🤖 Чат с ИИ-Тренером (Base64 Bypass)")
    
    if not REAL_API_KEY:
        st.warning("⚠️ ИИ заблокирован: Сначала вставь закодированный Base64 ключ в строку №31 кода!")
    else:
        now_kcal = sum(i["kcal"] for i in st.session_state.meal_bag)
        now_p = sum(i["p"] for i in st.session_state.meal_bag)
        
        system_prompt = f"""
        Ты — харизматичный ИИ-тренер по бодибилдингу. Консультируешь атлета {current_user}.
        Вес: {user_weight}кг, рост: {user_height}см. Цель калорий: {round(target_kcal)}.
        Сегодня съел: {round(now_kcal)} ккал, белка: {round(now_p)}г.
        Отвечай строго на языке пользователя, ультра-коротко, используя фитнес-сленг.
        """
        
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
        if user_input := st.chat_input("Спроси тренера..."):
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
                
            with st.chat_message("assistant"):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=system_prompt)
                    response = model.generate_content(user_input)
                    reply = response.text
                except Exception as e:
                    reply = f"Ошибка генерации. Проверь валидность ключа в Base64. Лог: {e}"
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})