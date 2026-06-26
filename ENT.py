import streamlit as st
import json
import os
from datetime import date
from foods import FOOD_DATABASE

# Настройки страницы
st.set_page_config(page_title="Масса-Комбайн 3000", page_icon="💪", layout="wide")

# Имя файла для хранения истории на сервере
HISTORY_FILE = "diet_history.json"

# Функция для загрузки истории из файла
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

# Функция для сохранения истории в файл
def save_history(history_data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_data, f, ensure_ascii=False, indent=4)

# Инициализация сессий
if "meal_bag" not in st.session_state:
    st.session_state.meal_bag = []
if "water_intake" not in st.session_state:
    st.session_state.water_intake = 0
if "history" not in st.session_state:
    st.session_state.history = load_history()

st.title("💪 Масса-Комбайн 3000 | Ультра Трекер & История Прогресса")
st.write("Научный комплекс для набора массы. Записывай рацион, контролируй воду и отслеживай прогресс по дням!")

# --- БОКОВАЯ ПАНЕЛЬ: Персональные Данные ---
st.sidebar.header("🎯 Персональные Данные")
user_gender = st.sidebar.radio("Пол:", ["Мужской", "Женский"])
user_age = st.sidebar.number_input("Возраст (лет):", min_value=12, max_value=80, value=22, step=1)
user_height = st.sidebar.number_input("Рост (см):", min_value=120, max_value=220, value=178, step=1)
user_weight = st.sidebar.number_input("Текущий вес (кг):", min_value=35, max_value=180, value=70, step=1)

activity_level = st.sidebar.selectbox("Уровень физической активности:", [
    "Минимальный (сидячая работа, без спорта)",
    "Легкий (1-3 тренировки в неделю)",
    "Средний (3-5 тренировок в неделю)",
    "Высокий (6-7 тяжелых тренировок в неделю)"
])

# Расчет нормы (Миффлин-Сан Жеора)
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
### 📊 Твоя Цель на Сутки:
* 🔥 Калории: **{round(target_kcal)} ккал**
* 🍗 Белки: **{round(target_p)} г**
* 🥑 Жиры: **{round(target_f)} г**
* 🍞 Углеводы: **{round(target_c)} г**
* 💧 Вода: **{target_water} л**
""")

# --- ВКЛАДКИ: Дневник и История прогресса (НОВАЯ ФИЧА) ---
tab_diary, tab_history = st.tabs(["📝 Дневник питания за сегодня", "📈 История и Прогресс"])

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
            placeholder="Начни писать: кола, бешбармак, казы...",
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
        
        w_col1, w_col2, w_col3 = st.columns(3)
        with w_col1:
            if st.button("🥛 Стакан (+250 мл)"):
                st.session_state.water_intake += 250
                st.rerun()
        with w_col2:
            if st.button("🍼 Бутылка (+500 мл)"):
                st.session_state.water_intake += 500
                st.rerun()
        with w_col3:
            if st.button("🗑️ Сбросить воду"):
                st.session_state.water_intake = 0
                st.rerun()
                
        st.progress(min(max(st.session_state.water_intake / (target_water * 1000), 0.0), 1.0))

    with col_right:
        st.subheader("📋 Дневник Питания за Сегодня")
        
        total_kcal = total_p = total_f = total_c = 0
        export_text = f"📋 МОЙ РАЦИОН НА МАССУ ({date.today()}):\n\n"
        
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
            st.markdown("### 📊 АНАЛИЗ И ИТОГИ СУТОК:")
            
            # Статус-вердикт
            if total_p < (target_p * 0.7):
                st.error("⚠️ Статус: КРИТИЧЕСКИ МАЛО БЕЛКА! Мышцы не растут!")
            elif total_kcal < maintenance_calories:
                st.warning("📉 Статус: Ты в дефиците калорий. Массы не будет!")
            else:
                st.success("🔥 Статус: ИДЕАЛЬНАЯ АНАБОЛИЧЕСКАЯ ЗОНА!")

            # Прогресс-бары
            st.write(f"🔥 Калории: {round(total_kcal)} / {round(target_kcal)} ккал")
            st.progress(min(max(total_kcal / target_kcal, 0.0), 1.0))
            st.write(f"🍗 Белки: {round(total_p, 1)} / {round(target_p)} г")
            st.progress(min(max(total_p / target_p, 0.0), 1.0))
            
            # ФИЧА: Кнопка сохранения дня в историю
            st.markdown("---")
            st.subheader("💾 Сохранение дня")
            if st.button("🔥 СОХРАНИТЬ ЭТОТ ДЕНЬ В ИСТОРИЮ", use_container_width=True, type="primary"):
                today_str = str(date.today())
                st.session_state.history[today_str] = {
                    "kcal": round(total_kcal),
                    "target_kcal": round(target_kcal),
                    "protein": round(total_p, 1),
                    "target_protein": round(target_p),
                    "water": st.session_state.water_intake,
                    "target_water": round(target_water * 1000)
                }
                save_history(st.session_state.history)
                st.balloons()
                st.success(f"🎉 Данные за {today_str} успешно сохранены во вкладку 'История'!")

            if st.button("Очистить Дневник 🗑️", type="secondary"):
                st.session_state.meal_bag = []
                st.session_state.water_intake = 0
                st.rerun()
        else:
            st.info("Твой дневник питания пока пуст.")

# === ВТОРЯ ВКЛАДКА: ИСТОРИЯ И ПРОГРЕСС ===
with tab_history:
    st.subheader("📈 Твой календарь успехов")
    
    if st.session_state.history:
        # Показываем краткую сводку по дням текстом
        st.write("Ниже представлена история дней, когда ты вел подсчет калорий:")
        
        # Сортируем дни по дате (свежие вверху)
        sorted_days = sorted(list(st.session_state.history.keys()), reverse=True)
        
        # Текстовый мини-график прогресса калорий для наглядности
        st.markdown("### 📊 График калорийности по дням:")
        for day in reversed(sorted_days[-7:]): # Показываем последние 7 записей в виде графика
            day_data = st.session_state.history[day]
            kcal = day_data["kcal"]
            tkcal = day_data["target_kcal"]
            
            # Строим визуальную полоску из символов
            bar_length = int((kcal / tkcal) * 20) if tkcal > 0 else 0
            bar_str = "🟩" * min(bar_length, 20) + "⬜" * max(20 - bar_length, 0)
            st.text(f"{day} | {bar_str} | {kcal} / {tkcal} ккал")
            
        st.markdown("---")
        
        # Выбор конкретного дня для детального просмотра
        st.markdown("### 🔍 Детальный просмотр конкретного дня")
        chosen_day = st.selectbox("Выбери дату для детального анализа:", sorted_days)
        
        if chosen_day:
            day_data = st.session_state.history[chosen_day]
            
            h_col1, h_col2, h_col3 = st.columns(3)
            with h_col1:
                st.metric("Съедено калорий", f"{day_data['kcal']} ккал", f"Цель: {day_data['target_kcal']}")
            with h_col2:
                st.metric("Получено белка", f"{day_data['protein']} г", f"Цель: {day_data['target_protein']}")
            with h_col3:
                st.metric("Выпито воды", f"{day_data['water']} мл", f"Цель: {day_data['target_water']}")
                
            # Прогресс-бары для выбранного дня в истории
            st.write("Выполнение нормы калорий в этот день:")
            st.progress(min(max(day_data['kcal'] / day_data['target_kcal'], 0.0), 1.0))
    else:
        st.info("📉 У тебя пока нет сохраненной истории. Заполни дневник питания на первой вкладке за сегодня и нажми кнопку 'Сохранить этот день в историю'!")