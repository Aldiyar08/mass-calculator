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

# === ВКЛАДКА 3: ЧАТ С ИИ-ТРЕНЕРОМ (МЫ ТУТ!) ===
with tab_ai:
    st.subheader("🤖 Твой Персональный ИИ-Тренер по Набору Массы")
    st.write("Привет! Я встроенный ИИ-эксперт. Анализирую твои параметры, рацион и даю чёткие фитнес-советы. Спрашивай меня обо всём!")

    # Краткая симуляция экспертного ИИ ответа на основе контекста
    # (В реальном проекте сюда подключается API-ключ OpenAI/Google, а пока мы пишем мощный локальный эмулятор-анализатор, который знает о пользователе ВСЁ)
    
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Напиши мне (например: 'Оцени мой рацион за сегодня', 'Как мне лучше тренироваться при моём росте?')"):
        # Добавляем вопрос пользователя в чат
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
            
        # Генерируем мега-умный контекстный ответ тренера
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            # Собираем данные для анализа
            current_kcal = sum(item["kcal"] for item in st.session_state.meal_bag)
            current_p = sum(item["p"] for item in st.session_state.meal_bag)
            
            # Логика ответов
            ui_lower = user_input.lower()
            if "рацион" in ui_lower or "оцени" in ui_lower or "еду" in ui_lower:
                ai_response = f"""🤖 **Анализирую твою тарелку на сегодня, {current_user}:**
                
Ты занёс в дневник **{round(current_kcal)} ккал** и **{round(current_p, 1)}г белка**. 
Твоя цель для набора массы: **{round(target_kcal)} ккал**. 

"""
                if current_kcal == 0:
                    ai_response += "Твой дневник сегодня пуст! Скорее добавь туда что-нибудь сытное (например, плов, казы, бананы или гейнер), чтобы запустить анаболизм."
                elif current_kcal < maintenance_calories:
                    ai_response += f"⚠️ Внимание! Ты съел меньше уровня удержания веса ({round(maintenance_calories)} ккал). Твой организм сейчас голодает и жжёт мышцы. Срочно добавь сложный углевод или белок!"
                elif current_kcal >= maintenance_calories and current_kcal < target_kcal:
                    ai_response += "Ты зашёл в зону поддержания, но для роста мышц нужно закинуть ещё 300-400 калорий. Добавь орехи или порцию протеина!"
                else:
                    ai_response += "🔥 Отличная работа! Ты в идеальном профиците. Мышцы получают максимум энергии для роста. Главное — не забывай про тяжёлые тренировки!"
                    
            elif "тренировк" in ui_lower or "спорт" in ui_lower or "мышц" in ui_lower:
                ai_response = f"""🤖 **Рекомендация по тренировкам под твои параметры:**
                
Учитывая твой рост (**{user_height} см**) и текущий вес (**{user_weight} кг**), тебе отлично подойдёт силовой сплит с упором на базовые многосуставные движения (Приседания, Становая тяга, Жим штанги лежа).
* Так как у тебя цель — набор массы, держи диапазон повторений в районе **8-12 раз** до близкого отказа.
* Отдыхай между подходами по 2-3 минуты, чтобы нервная система успевала восстановиться.
* Твой уровень активности заявлен как *"{activity_level}"*, поэтому убедись, что ты тренируешься тяжело, но не перегораешь!
"""
            else:
                ai_response = f"""🤖 Привет, {current_user}! Как твой личный ИИ-наставник, я изучил твой профиль:
* **Пол:** {user_gender} | **Возраст:** {user_age} лет
* **Рост/Вес:** {user_height}см / {user_weight}кг
* **Текущий рацион:** {round(current_kcal)} / {round(target_kcal)} ккал.

Твой вопрос: *"{user_input}"* — отличная тема! Для качественного набора веса старайся делать упор на плотную, богатую нутриентами пищу (крупы, мясо, яйца). Если хочешь, чтобы я оценил твоё питание, просто напиши слово **"рацион"**!
"""
            response_placeholder.markdown(ai_response)
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})