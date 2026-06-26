import streamlit as st
import json
import os
import hashlib
from datetime import date
import google.generativeai as genai
from foods import FOOD_DATABASE

# ====================== НАСТРОЙКИ СТРАНИЦЫ ======================
st.set_page_config(page_title="Масса-Комбайн ИИ", page_icon="🤖", layout="wide")

# ====================== ИНИЦИАЛИЗАЦИЯ GEMINI API ======================
GEMINI_API_KEY = None
if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"].strip():
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"].strip()
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
    genai.configure(api_key=GEMINI_API_KEY)
else:
    st.error("⚠️ GEMINI_API_KEY не найден в Streamlit Secrets!")

# ====================== ФАЙЛЫ БАЗ ДАННЫХ ======================
USERS_FILE = "users_db.json"
HISTORY_FILE = "users_history_db.json"

def load_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ====================== ИНИЦИАЛИЗАЦИЯ СЕССИИ ======================
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

users_db = load_json(USERS_FILE)
history_db = load_json(HISTORY_FILE)

# ====================== БЛОК АВТОРИЗАЦИИ ======================
if not st.session_state.logged_in:
    st.title("💪 Добро пожаловать в Масса-Комбайн ИИ!")
    st.write("Авторизуйся или создай аккаунт")

    auth_tab, reg_tab = st.tabs(["🔑 Вход", "📝 Регистрация"])

    with auth_tab:
        login_user = st.text_input("Логин:", key="login_u")
        login_pass = st.text_input("Пароль:", type="password", key="login_p")
        if st.button("Войти 🚀", use_container_width=True):
            if login_user in users_db and users_db[login_user]["password"] == hash_password(login_pass):
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.success(f"Добро пожаловать обратно, {login_user}!")
                st.rerun()
            else:
                st.error("Неверный логин или пароль")

    with reg_tab:
        reg_user = st.text_input("Придумай логин:", key="reg_u")
        reg_pass = st.text_input("Придумай пароль:", type="password", key="reg_p")
        if st.button("Создать аккаунт 🎉", use_container_width=True):
            if not reg_user or not reg_pass:
                st.warning("Заполните оба поля!")
            elif reg_user in users_db:
                st.error("Логин уже занят")
            else:
                users_db[reg_user] = {"password": hash_password(reg_pass)}
                save_json(USERS_FILE, users_db)
                st.session_state.logged_in = True
                st.session_state.username = reg_user
                st.success("Аккаунт успешно создан!")
                st.rerun()
    st.stop()

# ====================== ГЛАВНЫЙ ИНТЕРФЕЙС ======================
current_user = st.session_state.username

st.sidebar.write(f"👤 **{current_user}**")
if st.sidebar.button("Выйти 🚪", use_container_width=True):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.title(f"🏋️‍♂️ Масса-Комбайн ИИ | {current_user}")

# ====================== БОКОВАЯ ПАНЕЛЬ С ПАРАМЕТРАМИ ======================
st.sidebar.header("🎯 Твои параметры")
user_gender = st.sidebar.radio("Пол:", ["Мужской", "Женский"])
user_age = st.sidebar.number_input("Возраст (лет):", 12, 80, 18)
user_height = st.sidebar.number_input("Рост (см):", 120, 220, 188)
user_weight = st.sidebar.number_input("Вес (кг):", 35, 180, 71)

activity_level = st.sidebar.selectbox("Уровень активности:", [
    "Минимальный (сидячий образ lifestyle)",
    "Легкий (1-3 тренировки в неделю)",
    "Средний (3-5 тренировок в неделю)",
    "Высокий (6-7 тяжелых тренировок в неделю)"
])

# Расчёт BMR и целей
if user_gender == "Мужской":
    bmr = (10 * user_weight) + (6.25 * user_height) - (5 * user_age) + 5
else:
    bmr = (10 * user_weight) + (6.25 * user_height) - (5 * user_age) - 161

activity_coefs = {
    "Минимальный (сидячий образ lifestyle)": 1.2,
    "Легкий (1-3 тренировки в неделю)": 1.375,
    "Средний (3-5 тренировок в неделю)": 1.55,
    "Высокий (6-7 тяжелых тренировок в неделю)": 1.725
}

maintenance_calories = bmr * activity_coefs[activity_level]
target_kcal = maintenance_calories + 500
target_p = user_weight * (2.0 if user_gender == "Мужской" else 1.8)
target_f = user_weight * 1.0
target_c = (target_kcal - (target_p * 4) - (target_f * 9)) / 4
target_water = round((user_weight * 35) / 1000, 1)

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
### 📊 Суточные цели на массу:
**🔥 {round(target_kcal)} ккал**  
**🍗 {round(target_p)} г** белка  
**🥑 {round(target_f)} г** жиров  
**🍞 {round(target_c)} г** углеводов  
**💧 {target_water} л** воды
""")

if current_user not in history_db:
    history_db[current_user] = {}

# ====================== ВКЛАДКИ ======================
tab_diary, tab_history, tab_ai = st.tabs(["📝 Дневник питания", "📈 История", "🤖 ИИ-Тренер"])

# ====================== ВКЛАДКА 1: ДНЕВНИК ======================
with tab_diary:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("🔍 Добавление еды")
        meal_type = st.radio("Приём пищи:", ["Завтрак 🍳", "Обед 🍲", "Ужин 🥩", "Перекус 🍏"], horizontal=True)
        
        selected_product = st.selectbox(
            "Продукт:", 
            options=list(FOOD_DATABASE.keys()), 
            index=None, 
            placeholder="Начни вводить название..."
        )
        
        if selected_product:
            nutr = FOOD_DATABASE[selected_product]
            amount = st.number_input(f"Количество ({nutr['unit']}):", min_value=1, max_value=2000, value=150, step=10)
            
            if st.button("➕ Добавить в дневник", use_container_width=True):
                ratio = amount / 100.0
                st.session_state.meal_bag.append({
                    "meal_type": meal_type,
                    "name": selected_product,
                    "amount": amount,
                    "unit": nutr["unit"],
                    "kcal": nutr["калории"] * ratio,
                    "p": nutr["белки"] * ratio,
                    "f": nutr["жиры"] * ratio,
                    "c": nutr["углеводы"] * ratio
                })
                st.success(f"Добавлено в {meal_type}!")
                st.rerun()

        st.markdown("---")
        st.subheader("💧 Водный баланс")
        st.write(f"Выпито: **{st.session_state.water_intake} мл** из **{int(target_water * 1000)} мл**")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🥛 +250 мл", use_container_width=True):
                st.session_state.water_intake += 250
                st.rerun()
        with c2:
            if st.button("🍼 +500 мл", use_container_width=True):
                st.session_state.water_intake += 500
                st.rerun()
        with c3:
            if st.button("🗑️ Сбросить", use_container_width=True):
                st.session_state.water_intake = 0
                st.rerun()

    with col_right:
        st.subheader("📋 Записи за сегодня")
        total_kcal = total_p = total_f = total_c = 0
        export_text = f"РАЦИОН НА {date.today()}\n\n"

        for cat in ["Завтрак 🍳", "Обед 🍲", "Ужин 🥩", "Перекус 🍏"]:
            items = [i for i in st.session_state.meal_bag if i["meal_type"] == cat]
            if items:
                st.markdown(f"#### {cat}")
                export_text += f"--- {cat} ---\n"
                for item in items:
                    total_kcal += item["kcal"]
                    total_p += item["p"]
                    total_f += item["f"]
                    total_c += item["c"]
                    st.write(f"▪️ {item['name']} — {item['amount']} {item['unit']} | **{round(item['kcal'])} ккал**")
                    export_text += f"• {item['name']} ({item['amount']}{item['unit']}) — {round(item['kcal'])} ккал\n"

        if st.session_state.meal_bag or st.session_state.water_intake > 0:
            st.markdown("---")
            st.subheader("📊 Итог дня")
            st.write(f"🔥 Калории: {round(total_kcal)} / {round(target_kcal)}")
            st.progress(min(total_kcal / target_kcal, 1.0) if target_kcal > 0 else 0)
            st.write(f"🍗 Белки: {round(total_p, 1)} / {round(target_p)} г")
            st.progress(min(total_p / target_p, 1.0) if target_p > 0 else 0)
            st.write(f"🥑 Жиры: {round(total_f, 1)} / {round(target_f)} г")
            st.progress(min(total_f / target_f, 1.0) if target_f > 0 else 0)
            st.write(f"🍞 Углеводы: {round(total_c, 1)} / {round(target_c)} г")
            st.progress(min(total_c / target_c, 1.0) if target_c > 0 else 0)

            if st.button("🔥 СОХРАНИТЬ ДЕНЬ В ИСТОРИЮ", type="primary", use_container_width=True):
                today = str(date.today())
                history_db[current_user][today] = {
                    "kcal": round(total_kcal),
                    "target_kcal": round(target_kcal),
                    "protein": round(total_p, 1),
                    "target_protein": round(target_p),
                    "water": st.session_state.water_intake,
                    "target_water": int(target_water * 1000)
                }
                save_json(HISTORY_FILE, history_db)
                st.balloons()
                st.success("День успешно сохранён!")

            st.text_area("Отчёт для копирования:", export_text, height=150)

            if st.button("Очистить текущий дневник 🗑️"):
                st.session_state.meal_bag = []
                st.session_state.water_intake = 0
                st.rerun()

# ====================== ВКЛАДКА 2: ИСТОРИЯ ======================
with tab_history:
    st.subheader("📈 История питания")
    user_history = history_db.get(current_user, {})
    if user_history:
        st.write("Здесь будет график и архив (можно доработать позже)")
    else:
        st.info("Пока нет сохранённых дней. Сохрани первый день в дневнике.")

# ====================== ВКЛАДКА 3: ИИ-ТРЕНЕР ======================
# ====================== ВКЛАДКА 3: ИИ-ТРЕНЕР (ОБНОВЛЁННАЯ) ======================
with tab_ai:
    st.subheader("🤖 ИИ-Тренер (Gemini)")

    # === ОТЛАДКА КЛЮЧА (временно оставь) ===
    with st.expander("🔧 Debug: информация о ключе"):
        st.write("Ключ найден в st.secrets:", "GEMINI_API_KEY" in st.secrets)
        if "GEMINI_API_KEY" in st.secrets:
            key = st.secrets["GEMINI_API_KEY"].strip()
            st.write("Длина ключа:", len(key))
            st.write("Начинается с:", key[:8] + "..." if key else "пусто")
            st.write("Заканчивается на:", "..." + key[-6:] if key else "пусто")
        else:
            st.error("Ключ НЕ найден в Secrets!")

    # Текущие показатели
    now_kcal = sum(item["kcal"] for item in st.session_state.meal_bag)
    now_p = sum(item["p"] for item in st.session_state.meal_bag)
    now_f = sum(item["f"] for item in st.session_state.meal_bag)
    now_c = sum(item["c"] for item in st.session_state.meal_bag)

    system_prompt = f"""
Ты — жёсткий, но честный ИИ-тренер по набору массы.
Атлет: {current_user}, {user_gender}, {user_age} лет, {user_height} см, {user_weight} кг.
Цели на день: {round(target_kcal)} ккал | Б: {round(target_p)}г | Ж: {round(target_f)}г | У: {round(target_c)}г
Сегодня съел: {round(now_kcal)} ккал | Б: {round(now_p)}г | Ж: {round(now_f)}г | У: {round(now_c)}г
Выпито воды: {st.session_state.water_intake} мл

Отвечай коротко, по делу, на русском языке. Используй фитнес-сленг.
"""

    # История чата
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Напиши тренеру..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            if not ("GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"].strip()):
                reply = "❌ Ключ не найден в Secrets. Добавь его по инструкции выше."
            else:
                try:
                    # Конфигурируем ключ заново перед каждым запросом (более надёжно)
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"].strip())
                    
                    model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        system_instruction=system_prompt
                    )
                    response = model.generate_content(user_input)
                    reply = response.text
                except Exception as e:
                    reply = f"❌ Ошибка Gemini: {str(e)}"

            st.markdown(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})