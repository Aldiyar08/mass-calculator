import streamlit as st
import json
import os
import hashlib
from datetime import date
from foods import FOOD_DATABASE

# Настройки страницы
st.set_page_config(page_title="Масса-Комбайн ИИ", page_icon="🤖", layout="wide")

# Имена файлов для данных на сервере
USERS_FILE = "users_db.json"
HISTORY_FILE = "users_history_db.json"

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ БАЗЫ ДАННЫХ ---
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

# Инициализация глобального состояния сессии
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

# Загружаем базы данных с диска
users_db = load_json(USERS_FILE)
history_db = load_json(HISTORY_FILE)

# --- ОКНО АВТОРИЗАЦИИ И РЕГИСТРАЦИИ ---
if not st.session_state.logged_in:
    st.title("💪 Добро пожаловать в Масса-Комбайн ИИ!")
    st.write("Для входа в личный кабинет и общения с ИИ-тренером, пожалуйста, авторизуйтесь.")
    
    auth_tab, reg_tab = st.tabs(["🔑 Вход", "📝 Регистрация"])
    
    with auth_tab:
        login_user = st.text_input("Логин (Вход):", key="login_u")
        login_pass = st.text_input("Пароль (Вход):", type="password", key="login_p")
        if st.button("Войти 🚀", use_container_width=True):
            if login_user in users_db and users_db[login_user]["password"] == hash_password(login_pass):
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.success(f"Рады возвращению, {login_user}!")
                st.rerun()
            else:
                st.error("Неверный логин или пароль!")
                
    with reg_tab:
        reg_user = st.text_input("Придумайте логин:", key="reg_u")
        reg_pass = st.text_input("Придумайте пароль:", type="password", key="reg_p")
        if st.button("Создать аккаунт 🎉", use_container_width=True):
            if not reg_user or not reg_pass:
                st.warning("Заполните все поля!")
            elif reg_user in users_db:
                st.error("Такой логин уже занят!")
            else:
                users_db[reg_user] = {"password": hash_password(reg_pass)}
                save_json(USERS_FILE, users_db)
                st.success("Аккаунт успешно создан! Теперь войдите во вкладке 'Вход'.")
                
    st.stop() # Останавливаем выполнение кода ниже, если пользователь не вошел

# --- КОД ДЛЯ АВТОРИЗОВАННЫХ ПОЛЬЗОВАТЕЛЕЙ ---
current_user = st.session_state.username

# Выход из аккаунта кнопкой в углу
st.sidebar.write(f"👤 Вы вошли как: **{current_user}**")
if st.sidebar.button("Выйти из аккаунта 🚪"):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.meal_bag = []
    st.session_state.water_intake = 0
    st.session_state.chat_history = []
    st.rerun()

st.title(f"💪 Масса-Комбайн ИИ | Личный кабинет {current_user}")

# --- БОКОВАЯ ПАНЕЛЬ: Персональные Данные ---
st.sidebar.header("🎯 Твои Параметры")
user_gender = st.sidebar.radio("Пол:", ["Мужской", "Женский"])
user_age = st.sidebar.number_input("Возраст (лет):", min_value=12, max_value=80, value=22, step=1, key="age_u")
user_height = st.sidebar.number_input("Рост (см):", min_value=120, max_value=220, value=178, step=1, key="height_u")
user_weight = st.sidebar.number_input("Текущий вес (кг):", min_value=35, max_value=180, value=70, step=1, key="weight_u")

activity_level = st.sidebar.selectbox("Уровень активности:", [
    "Минимальный (сидячая работа, без спорта)",
    "Легкий (1-3 тренировки в неделю)",
    "Средний (3-5 тренировок в неделю)",
    "Высокий (6-7 тяжелых тренировок в неделю)"
])

# Расчет нормы КБЖУ (Формула Миффлина-Сан Жеора)
if user_gender == "Мужской":
    bmr = (10 * user_weight) + (6.25 * user_height) - (5 * user_age) + 5
else:
    bmr = (10 * user_weight) + (6.25 * user_height) - (5 * user_age) - 161

activity_coefs = {
    "Минимальный (сидячая работа, без спорта)": 1.2,
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
### 📊 Цель на Сутки:
* 🔥 Калории: **{round(target_kcal)} ккал**
* 🍗 Белки: **{round(target_p)} г**
* 🥑 Жиры: **{round(target_f)} г**
* 🍞 Углеводы: **{round(target_c)} г**
* 💧 Вода: **{target_water} л**
""")

# --- ТРИ ГЛАВНЫЕ ВКЛАДКИ ПЛАТФОРМЫ ---
tab_diary, tab_history, tab_ai = st.tabs(["📝 Дневник питания", "📈 Моя История", "🤖 Чат с ИИ-Тренером"])

# Инициализируем локальную историю пользователя
if current_user not in history_db:
    history_db[current_user] = {}

# === ВКЛАДКА 1: ДНЕВНИК ПИТАНИЯ ===
with tab_diary:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("🔍 Добавление продуктов")
        meal_type = st.radio("Куда добавляем?", ["Завтрак 🍳", "Обед 🍲", "Ужин 🥩", "Перекус 🍏"], horizontal=True)
        
        options = list(FOOD_DATABASE.keys())
        selected_product = st.selectbox(
            "Ищи продукт с автоподбором:",
            options=options,
            index=None,
            placeholder="Начни писать: кола, плов, гейнер...",
        )

        if selected_product:
            unit = FOOD_DATABASE[selected_product]["unit"]
            nutr = FOOD_DATABASE[selected_product]
            
            st.caption(f"📊 КБЖУ на 100г/мл: {nutr['калории']} ккал | Б: {nutr['белки']}г | Ж: {nutr['жиры']}г | У: {nutr['углеводы']}г")
            amount = st.number_input(f"Укажи количество ({unit}):", min_value=1, max_value=2000, value=150, step=10)
            
            if st.button("Записать в дневник ➕", use_container_width=True):
                ratio = amount / 100.0
                st.session_state.meal_bag.append({
                    "meal_type": meal_type,
                    "name": selected_product,
                    "amount": amount,
                    "unit": unit,
                    "kcal": nutr["калории"] * ratio,
                    "p": nutr["белки"] * ratio,
                    "f": nutr["жиры"] * ratio,
                    "c": nutr["углеводы"] * ratio
                })
                st.success(f"✅ Добавлено в {meal_type}!")

        st.markdown("---")
        st.subheader("💧 Водный баланс")
        st.write(f"Выпито: **{st.session_state.water_intake} мл** из **{round(target_water * 1000)} мл**")
        
        w_col1, w_col2 = st.columns(2)
        with w_col1:
            if st.button("🥛 Стакан (+250 мл)"):
                st.session_state.water_intake += 250
                st.rerun()
        with w_col2:
            if st.button("🍼 Бутылка (+500 мл)"):
                st.session_state.water_intake += 500
                st.rerun()

    with col_right:
        st.subheader("📋 Рацион за Сегодня")
        
        total_kcal = total_p = total_f = total_c = 0
        categories = ["Завтрак 🍳", "Обед 🍲", "Ужин 🥩", "Перекус 🍏"]
        
        for cat in categories:
            cat_items = [item for item in st.session_state.meal_bag if item["meal_type"] == cat]
            if cat_items:
                st.markdown(f"#### {cat}")
                for item in cat_items:
                    total_kcal += item["kcal"]
                    total_p += item["p"]
                    total_f += item["f"]
                    total_c += item["c"]
                    st.write(f"▪️ *{item['name']}* — {item['amount']} {item['unit']} | **{round(item['kcal'])} ккал**")

        if st.session_state.meal_bag or st.session_state.water_intake > 0:
            st.markdown("---")
            st.markdown("### 📊 ИТОГИ СУТОК:")

            st.write(f"🔥 Калории: {round(total_kcal)} / {round(target_kcal)} ккал")
            st.progress(min(max(total_kcal / target_kcal, 0.0), 1.0))
            st.write(f"🍗 Белки: {round(total_p, 1)} / {round(target_p)} г")
            st.progress(min(max(total_p / target_p, 0.0), 1.0))
            
            st.markdown("---")
            if st.button("🔥 СОХРАНИТЬ ДЕНЬ В ЛИЧНУЮ ИСТОРИЮ", use_container_width=True, type="primary"):
                today_str = str(date.today())
                history_db[current_user][today_str] = {
                    "kcal": round(total_kcal),
                    "target_kcal": round(target_kcal),
                    "protein": round(total_p, 1),
                    "target_protein": round(target_p),
                    "water": st.session_state.water_intake
                }
                save_json(HISTORY_FILE, history_db)
                st.balloons()
                st.success("Данные сохранены в твой личный профиль!")

            if st.button("Очистить Дневник 🗑️", type="secondary"):
                st.session_state.meal_bag = []
                st.session_state.water_intake = 0
                st.rerun()
        else:
            st.info("Твой дневник питания пока пуст.")

# === ВКЛАДКА 2: ИСТОРИЯ И ПРОГРЕСС (ЛИЧНАЯ) ===
with tab_history:
    st.subheader(f"📈 История успехов пользователя {current_user}")
    user_history = history_db[current_user]
    
    if user_history:
        sorted_days = sorted(list(user_history.keys()), reverse=True)
        
        st.markdown("### 📊 График калорийности (Последние дни):")
        for day in reversed(sorted_days[-7:]):
            day_data = user_history[day]
            bar_length = int((day_data["kcal"] / day_data["target_kcal"]) * 20) if day_data["target_kcal"] > 0 else 0
            bar_str = "🟩" * min(bar_length, 20) + "⬜" * max(20 - bar_length, 0)
            st.text(f"{day} | {bar_str} | {day_data['kcal']} / {day_data['target_kcal']} ккал")
            
        st.markdown("---")
        chosen_day = st.selectbox("Выбери дату для просмотра деталей:", sorted_days)
        if chosen_day:
            day_data = user_history[chosen_day]
            h_col1, h_col2 = st.columns(2)
            h_col1.metric("Съедено калорий", f"{day_data['kcal']} ккал", f"Цель: {day_data['target_kcal']}")
            h_col2.metric("Получено белка", f"{day_data['protein']} г", f"Цель: {day_data['target_protein']}")
    else:
        st.info("У тебя пока нет сохранённых дней. Сохрани сегодняшний рацион на первой вкладке!")

# === ВКЛАДКА 3: ЧАТ С НАСТОЯЩИМ ИИ-ТРЕНЕРОМ ===
with tab_ai:
    st.subheader("🤖 Твой Персональный ИИ-Тренер (На базе Google Gemini)")
    st.write("Теперь это настоящая нейросеть. Я вижу твои параметры, твой рацион и отвечу на любой вопрос!")

    # Подключаем библиотеку для работы с ИИ (ее нужно будет добавить в requirements.txt)
    try:
        import google.generativeai as genai
        
        # Укажи здесь свой API-ключ, полученный в Google AI Studio
        # Если заливаешь на GitHub, лучше использовать st.secrets["GEMINI_API_KEY"]
        GEMINI_API_KEY = "AQ.Ab8RN6IBNw0va2wtxDnpjCKVW_RkSwau78SeRfQjGhvPXrUYow" 
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        ai_available = True
    except Exception as e:
        st.error(f"Ошибка настройки ИИ: {e}")
        ai_available = False

    # Отображение истории чата
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Спроси что угодно: про программу тренировок, про калории, креатин или читмил..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            if ai_available and GEMINI_API_KEY != "AQ.Ab8RN6IBNw0va2wtxDnpjCKVW_RkSwau78SeRfQjGhvPXrUYow":
                # Собираем контекст о пользователе, чтобы ИИ знал всё о его прогрессе
                current_kcal = sum(item["kcal"] for item in st.session_state.meal_bag)
                current_p = sum(item["p"] for item in st.session_state.meal_bag)
                current_f = sum(item["f"] for item in st.session_state.meal_bag)
                current_c = sum(item["c"] for item in st.session_state.meal_bag)
                
                # Создаем системный промпт (инструкцию для ИИ), заставляя его быть тренером
                system_context = f"""
                Ты — жесткий, но мотивирующий ИИ-тренер по набору мышечной массы и фитнесу. 
                Ты общаешься с пользователем по имени {current_user}.
                Параметры пользователя: пол {user_gender}, возраст {user_age} лет, рост {user_height} см, вес {user_weight} кг, активность: {activity_level}.
                Его цель на сегодня: калории {round(target_kcal)}, белки {round(target_p)}г, жиры {round(target_f)}г, углеводы {round(target_c)}г.
                Что он уже съел сегодня: калории {round(current_kcal)} ккал, белки {round(current_p)}г, жиры {round(current_f)}г, углеводы {round(current_c)}г.
                Выпито воды: {st.session_state.water_intake} мл.
                
                Отвечай кратко, емко, по делу, используй фитнес-сленг, давай четкие научные расклады. Если он не добирает белка или калорий — мотивируй его поесть (особенно конину, плов, казы, творог). Отвечай на том же языке, на котором обратился пользователь.
                """
                
                try:
                    # Отправляем запрос в настоящую нейросеть вместе с контекстом
                    full_prompt = f"{system_context}\n\nВопрос пользователя: {user_input}\nОтвет тренера:"
                    response = model.generate_content(full_prompt)
                    ai_response = response.text
                except Exception as ex:
                    ai_response = f"🤖 Ой, не удалось связаться с мозгом ИИ. Ошибка: {ex}"
            else:
                ai_response = "🤖 Ключ API не настроен. Настоящий ИИ отключен, работает старый глупый бот."

            response_placeholder.markdown(ai_response)
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})