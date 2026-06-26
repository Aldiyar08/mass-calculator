import streamlit as st
import json
import os
import hashlib
from datetime import date
import google.generativeai as genai
from foods import FOOD_DATABASE

# 1. Настройки страницы
st.set_page_config(page_title="Масса-Комбайн ИИ", page_icon="🤖", layout="wide")

# 2. ЖЕСТКАЯ СИСЕМНАЯ ИНЪЕКЦИЯ КЛЮЧА (План Перехват)
if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"].strip() != "":
    # Насильно пихаем ключ в переменные окружения операционной системы Linux на сервере
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"].strip()
    # И дублируем прямым вызовом конфигурации
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
else:
    st.error("⚠️ Переменная GEMINI_API_KEY не найдена в Secrets!")

# Имена файлов для базы данных
USERS_FILE = "users_db.json"
HISTORY_FILE = "users_history_db.json"
# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ДАННЫМИ ---
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

# Инициализация сессионных переменных Streamlit
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

# Загружаем базы из файлов
users_db = load_json(USERS_FILE)
history_db = load_json(HISTORY_FILE)

# --- ИНТЕРФЕЙС АВТОРИЗАЦИИ / РЕГИСТРАЦИИ ---
if not st.session_state.logged_in:
    st.title("💪 Добро пожаловать в Масса-Комбайн ИИ!")
    st.write("Авторизуйся или создай аккаунт, чтобы получить доступ к умному дневнику питания и ИИ-тренеру.")
    
    auth_tab, reg_tab = st.tabs(["🔑 Вход в аккаунт", "📝 Регистрация профиля"])
    
    with auth_tab:
        login_user = st.text_input("Логин:", key="login_u")
        login_pass = st.text_input("Пароль:", type="password", key="login_p")
        if st.button("Войти в систему 🚀", use_container_width=True):
            if login_user in users_db and users_db[login_user]["password"] == hash_password(login_pass):
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.success(f"Успешный вход! Рады видеть тебя снова, {login_user}!")
                st.rerun()
            else:
                st.error("Ошибка: Неверный логин или пароль.")
                
    with reg_tab:
        reg_user = st.text_input("Придумай уникальный логин:", key="reg_u")
        reg_pass = st.text_input("Придумай сложный пароль:", type="password", key="reg_p")
        if st.button("Создать новый аккаунт 🎉", use_container_width=True):
            if not reg_user or not reg_pass:
                st.warning("Пожалуйста, заполните оба поля!")
            elif reg_user in users_db:
                st.error("Этот логин уже занят кем-то другим.")
            else:
                users_db[reg_user] = {"password": hash_password(reg_pass)}
                save_json(USERS_FILE, users_db)
                st.session_state.logged_in = True
                st.session_state.username = reg_user
                st.success("Аккаунт успешно создан! Добро пожаловать!")
                st.rerun()
                
    st.stop()  # Останавливаем выполнение кода для неавторизованных

# --- ГЛАВНЫЙ ЭКРАН (Для авторизованных пользователей) ---
current_user = st.session_state.username

# Боковая панель управления профилем
st.sidebar.write(f"👤 Текущий профиль: **{current_user}**")
if st.sidebar.button("Выйти из аккаунта 🚪", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.meal_bag = []
    st.session_state.water_intake = 0
    st.session_state.chat_history = []
    st.rerun()

st.title(f"🏋️‍♂️ Масса-Комбайн ИИ | Панель {current_user}")

# --- БОКОВАЯ ПАНЕЛЬ: Калькулятор Миффлина-Сан Жеора ---
st.sidebar.header("🎯 Твои Физические Параметры")
user_gender = st.sidebar.radio("Пол:", ["Мужской", "Женский"])
user_age = st.sidebar.number_input("Возраст (лет):", min_value=12, max_value=80, value=18, step=1)
user_height = st.sidebar.number_input("Рост (см):", min_value=120, max_value=220, value=188, step=1)
user_weight = st.sidebar.number_input("Текущий вес (кг):", min_value=35, max_value=180, value=71, step=1)

activity_level = st.sidebar.selectbox("Уровень физических нагрузок:", [
    "Минимальный (сидячий образ lifestyle)",
    "Легкий (1-3 тренировки в неделю)",
    "Средний (3-5 тренировок в неделю)",
    "Высокий (6-7 тяжелых тренировок в неделю)"
])

# Вычисление базального метаболизма (BMR)
if user_gender == "Мужской":
    bmr = (10 * user_weight) + (6.25 * user_height) - (5 * user_age) + 5
else:
    bmr = (10 * user_weight) + (6.25 * user_height) - (5 * user_age) - 161

# Коэффициенты активности
activity_coefs = {
    "Минимальный (сидячий образ lifestyle)": 1.2,
    "Легкий (1-3 тренировки в неделю)": 1.375,
    "Средний (3-5 тренировок в неделю)": 1.55,
    "Высокий (6-7 тяжелых тренировок в неделю)": 1.725
}
maintenance_calories = bmr * activity_coefs[activity_level]

# План макронутриентов на профицит (+500 ккал) для набора массы
target_kcal = maintenance_calories + 500
target_p = user_weight * (2.0 if user_gender == "Мужской" else 1.8)
target_f = user_weight * 1.0
target_c = (target_kcal - (target_p * 4) - (target_f * 9)) / 4
target_water = round((user_weight * 35) / 1000, 1)

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
### 📊 Твоя суточная цель на массу:
* 🔥 Калории: **{round(target_kcal)} ккал**
* 🍗 Белки: **{round(target_p)} г**
* 🥑 Жиры: **{round(target_f)} г**
* 🍞 Углеводы: **{round(target_c)} г**
* 💧 Вода: **{target_water} л**
""")

if current_user not in history_db:
    history_db[current_user] = {}

# --- ВКАЛДКИ ИНТЕРФЕЙСА ---
tab_diary, tab_history, tab_ai = st.tabs(["📝 Дневник питания", "📈 Моя История по дням", "🤖 Чат с Настоящим ИИ-Тренером"])

# === ВКЛАДКА 1: ДНЕВНИК ПИТАНИЯ И ВОДЫ ===
with tab_diary:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("🔍 Добавление еды")
        meal_type = st.radio("Приём пищи:", ["Завтрак 🍳", "Обед 🍲", "Ужин 🥩", "Перекус 🍏"], horizontal=True)
        
        options = list(FOOD_DATABASE.keys())
        selected_product = st.selectbox(
            "Начни вводить название (работает автоподбор):",
            options=options,
            index=None,
            placeholder="Пример: кола, плов, гейнер, конина...",
        )

        if selected_product:
            unit = FOOD_DATABASE[selected_product]["unit"]
            nutr = FOOD_DATABASE[selected_product]
            
            st.caption(f"📊 КБЖУ на 100г/мл: {nutr['калории']} ккал | Б: {nutr['белки']}г | Ж: {nutr['жиры']}г | У: {nutr['углеводы']}г")
            amount = st.number_input(f"Укажи вес/объем ({unit}):", min_value=1, max_value=2000, value=150, step=10)
            
            if st.button("Добавить в дневник ➕", use_container_width=True):
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
                st.success(f"✅ Успешно занесено в категорию {meal_type}!")
                st.rerun()

        st.markdown("---")
        st.subheader("💧 Водный Баланс")
        st.write(f"Выпито за сегодня: **{st.session_state.water_intake} мл** из **{round(target_water * 1000)} мл**")
        
        w_col1, w_col2, w_col3 = st.columns(3)
        with w_col1:
            if st.button("🥛 Стакан (+250 мл)", use_container_width=True):
                st.session_state.water_intake += 250
                st.rerun()
        with w_col2:
            if st.button("🍼 Бутылка (+500 мл)", use_container_width=True):
                st.session_state.water_intake += 500
                st.rerun()
        with w_col3:
            if st.button("🗑️ Сбросить воду", use_container_width=True, type="secondary"):
                st.session_state.water_intake = 0
                st.rerun()
                
        st.progress(min(max(st.session_state.water_intake / (target_water * 1000), 0.0), 1.0))

    with col_right:
        st.subheader("📋 Записи за сегодня")
        
        total_kcal = total_p = total_f = total_c = 0
        export_text = f"📋 МОЙ ТРЕНИРОВОЧНЫЙ РАЦИОН ({date.today()}):\n\n"
        
        categories = ["Завтрак 🍳", "Обед 🍲", "Ужин 🥩", "Перекус 🍏"]
        for cat in categories:
            cat_items = [item for item in st.session_state.meal_bag if item["meal_type"] == cat]
            if cat_items:
                st.markdown(f"#### {cat}")
                export_text += f"--- {cat} ---\n"
                for item in cat_items:
                    total_kcal += item["kcal"]
                    total_p += item["p"]
                    total_f += item["f"]
                    total_c += item["c"]
                    st.write(f"▪️ *{item['name']}* — {item['amount']} {item['unit']} | **{round(item['kcal'])} ккал**")
                    export_text += f"• {item['name']} ({item['amount']}{item['unit']}) — {round(item['kcal'])} ккал\n"
                export_text += "\n"

        if st.session_state.meal_bag or st.session_state.water_intake > 0:
            st.markdown("---")
            st.markdown("### 📊 ВЫПОЛНЕНИЕ ПЛАНА КБЖУ:")

            st.write(f"🔥 Калории: {round(total_kcal)} / {round(target_kcal)} ккал")
            st.progress(min(max(total_kcal / target_kcal, 0.0), 1.0))
            st.write(f"🍗 Белки: {round(total_p, 1)} / {round(target_p)} г")
            st.progress(min(max(total_p / target_p, 0.0), 1.0))
            st.write(f"🥑 Жиры: {round(total_f, 1)} / {round(target_f)} г")
            st.progress(min(max(total_f / target_f, 0.0), 1.0))
            st.write(f"🍞 Углеводы: {round(total_c, 1)} / {round(target_c)} г")
            st.progress(min(max(total_c / target_c, 0.0), 1.0))
            
            export_text += f"ИТОГО ЗА СУТКИ:\n🔥 Калории: {round(total_kcal)}/{round(target_kcal)} ккал\n🍗 Белки: {round(total_p)}г\n🥑 Жиры: {round(total_f)}г\n🍞 Углеводы: {round(total_c)}г\n💧 Вода: {st.session_state.water_intake}мл"
            
            st.markdown("---")
            st.subheader("💾 Управление Дневником")
            
            if st.button("🔥 ФИКСИРОВАТЬ И СОХРАНИТЬ ДЕНЬ В ИСТОРИЮ", use_container_width=True, type="primary"):
                today_str = str(date.today())
                history_db[current_user][today_str] = {
                    "kcal": round(total_kcal),
                    "target_kcal": round(target_kcal),
                    "protein": round(total_p, 1),
                    "target_protein": round(target_p),
                    "water": st.session_state.water_intake,
                    "target_water": round(target_water * 1000)
                }
                save_json(HISTORY_FILE, history_db)
                st.balloons()
                st.success("Данные успешно сохранены в твой личный календарь прогресса!")

            st.text_area("Скопируй отчет для тренера или в Telegram:", value=export_text, height=120)

            if st.button("Очистить текущий дневник 🗑️", type="secondary", use_container_width=True):
                st.session_state.meal_bag = []
                st.session_state.water_intake = 0
                st.rerun()
        else:
            st.info("Твой текущий рацион пуст. Выбирай еду в левой колонке.")

# === ВКЛАДКА 2: ЛИЧНАЯ ИСТОРИЯ И КАЛЕНДАРЬ УСПЕХОВ ===
with tab_history:
    st.subheader(f"📈 Архив питания пользователя {current_user}")
    user_history = history_db.get(current_user, {})
    
    if user_history:
        sorted_days = sorted(list(user_history.keys()), reverse=True)
        
        st.markdown("### 📊 График калорийности за последние дни:")
        for day in reversed(sorted_days[-7:]):
            day_data = user_history[day]
            bar_length = int((day_data["kcal"] / day_data["target_kcal"]) * 20) if day_data.get("target_kcal", 0) > 0 else 0
            bar_str = "🟩" * min(bar_length, 20) + "⬜" * max(20 - bar_length, 0)
            st.text(f"{day} | {bar_str} | {day_data['kcal']} / {day_data['target_kcal']} ккал")
            
        st.markdown("---")
        chosen_day = st.selectbox("Выбери конкретную дату из архива:", sorted_days)
        if chosen_day:
            day_data = user_history[chosen_day]
            h_col1, h_col2, h_col3 = st.columns(3)
            h_col1.metric("Калории", f"{day_data['kcal']} ккал", f"Цель: {day_data.get('target_kcal', 0)}")
            h_col2.metric("Белки", f"{day_data['protein']} г", f"Цель: {day_data.get('target_protein', 0)}")
            h_col3.metric("Вода", f"{day_data['water']} мл")
            
            st.write("Выполнение суточной калорийности:")
            st.progress(min(max(day_data['kcal'] / day_data.get('target_kcal', 1), 0.0), 1.0))
    else:
        st.info("У тебя пока нет сохранённых дней. Сделай записи в дневнике питания и сохрани их!")

# === ВКЛАДКА 3: НАСТОЯЩИЙ ИИ-ТРЕНЕР GOOGLE GEMINI ===
with tab_ai:
    st.write("DEBUG: Ключ настроен?", "GEMINI_API_KEY" in st.secrets)
if "GEMINI_API_KEY" in st.secrets:
    key_preview = st.secrets["GEMINI_API_KEY"][:10] + "..." 
    st.write("DEBUG: Превью ключа:", key_preview)
    st.subheader("🤖 Твой Мощный ИИ-Наставник (На базе Google Gemini API)")
    st.write("Я полностью интегрирован в приложение: вижу твой рост, вес, дефицит или профицит и помогу составить идеальную диету.")

    ai_ready = False
    model = None
    
    # Считаем текущий прогресс для передачи динамического контекста в промпт
    now_kcal = sum(item["kcal"] for item in st.session_state.meal_bag)
    now_p = sum(item["p"] for item in st.session_state.meal_bag)
    now_f = sum(item["f"] for item in st.session_state.meal_bag)
    now_c = sum(item["c"] for item in st.session_state.meal_bag)

    # Системные инструкции для ИИ (задают характер тренера и передают КБЖУ данные)
    system_prompt = f"""
    Ты — харизматичный, экспертный, но прямолинейный ИИ-тренер по бодибилдингу и набору мышечной массы.
    Ты консультируешь атлета по имени {current_user}.
    Параметры атлета: пол {user_gender}, возраст {user_age} лет, рост {user_height} см, вес {user_weight} кг, уровень активности: {activity_level}.
    Его расчетные суточные цели для набора массы: калории {round(target_kcal)} ккал, белки {round(target_p)}г, жиры {round(target_f)}г, углеводы {round(target_c)}г.
    Что он съел по факту сегодня: калории {round(now_kcal)} ккал, белки {round(now_p)}г, жиры {round(now_f)}г, углеводы {round(now_c)}г.
    Выпито воды сегодня: {st.session_state.water_intake} мл.
    
    Твоя задача — давать четкие, научно обоснованные спортивные советы. Если пользователь не добирает белка — ругай его и мотивируй есть качественные продукты (конину, плов, казы, творог). Отвечай коротко, по делу, используй фитнес-сленг. Отвечай строго на том языке, на котором пишет пользователь.
    """

    try:
        # Проверяем, настроен ли genai на самом верху
        if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"].strip() != "":
            # Создаем модель, передавая системный промпт
            model = genai.GenerativeModel('gemini-1.5-flash-latest', system_instruction=system_prompt)
            ai_ready = True
    except Exception as e:
        st.error(f"Не удалось запустить модель ИИ: {e}")

    # Вывод истории диалога
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Напиши ИИ-тренеру (Например: 'Разбери мой рацион на сегодня', 'Что съесть до тренировки?')"):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        with st.chat_message("assistant"):
            response_box = st.empty()
            
            if ai_ready and model:
                try:
                    # Чистый вызов генерации (весь системный контекст подтягивается автоматически)
                    response = model.generate_content(user_input)
                    final_reply = response.text
                except Exception as ex:
                    final_reply = f"🤖 Произошел сбой при генерации ответа: {ex}"
            else:
                final_reply = "🤖 Ключ API не настроен в Streamlit Secrets или указан неверно. Пожалуйста, проверь вкладку Secrets в настройках сайта."

            response_box.markdown(final_reply)
            st.session_state.chat_history.append({"role": "assistant", "content": final_reply})