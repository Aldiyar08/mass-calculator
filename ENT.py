import streamlit as st
from foods import FOOD_DATABASE

# Настройки страницы
st.set_page_config(page_title="Масса-Комбайн 3000", page_icon="💪", layout="wide")

# Инициализация сессий
if "meal_bag" not in st.session_state:
    st.session_state.meal_bag = []
if "water_intake" not in st.session_state:
    st.session_state.water_intake = 0

st.title("💪 Масса-Комбайн 3000 | Ультра Трекер Рациона")
st.write("Профессиональный научный комплекс для набора массы, контроля КБЖУ, воды и экспорта диеты.")

# --- БОКОВАЯ ПАНЕЛЬ: Ультра-точный научный расчёт ---
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

# Формула Миффлина-Сан Жеора
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

# Профицит для набора массы (+500 ккал)
target_kcal = maintenance_calories + 500
target_p = user_weight * (2.0 if user_gender == "Мужской" else 1.8)
target_f = user_weight * 1.0
target_c = (target_kcal - (target_p * 4) - (target_f * 9)) / 4
target_water = round((user_weight * 35) / 1000, 1) # 35 мл на 1 кг веса

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
### 📊 Твоя Цель на Сутки:
* 🔥 Калории: **{round(target_kcal)} ккал**
* 🍗 Белки: **{round(target_p)} г**
* 🥑 Жиры: **{round(target_f)} г**
* 🍞 Углеводы: **{round(target_c)} г**
* 💧 Вода: **{target_water} л**
""")

# --- ОСНОВНОЙ ИНТЕРФЕЙС ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🔍 Добавление продуктов в Дневник")
    
    # Выбор категории приёма пищи (Фишка №1)
    meal_type = st.radio("Куда добавляем?", ["Завтрак 🍳", "Обед 🍲", "Ужин 🥩", "Перекус 🍏"], horizontal=True)
    
    options = list(FOOD_DATABASE.keys())
    selected_product = st.selectbox(
        "Ищи продукт со встроенным автоподбором Google-style:",
        options=options,
        index=None,
        placeholder="Начни писать: кола, бешбармак, казы, гейнер...",
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

    # Фишка №3: Водный трекер
    st.markdown("---")
    st.subheader("💧 Контроль Гидратации (Водный баланс)")
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
        if st.button("🗑️ Сбросить воду", type="secondary"):
            st.session_state.water_intake = 0
            st.rerun()
            
    water_progress = min(max(st.session_state.water_intake / (target_water * 1000), 0.0), 1.0)
    st.progress(water_progress)

with col_right:
    st.subheader("📋 Дневник Питания за Сегодня")
    
    # Считаем итоги
    total_kcal = total_p = total_f = total_c = 0
    export_text = "📋 МОЙ РАЦИОН НА МАССУ:\n\n"
    
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

    if st.session_state.meal_bag:
        st.markdown("---")
        st.markdown("### 📊 АНАЛИЗ И ИТОГИ СУТОК:")
        
        # Фишка №4: Статус-вердикт
        if total_p < (target_p * 0.7):
            st.error("⚠️ Статус: КРИТИЧЕСКИ МАЛО БЕЛКА! Мышцы не растут. Добавь конины, творога или протеина!")
        elif total_kcal < maintenance_calories:
            st.warning("📉 Статус: Ты в дефиците. Организм жжёт мышцы ради энергии, а не растит их. Ешь больше!")
        elif total_kcal >= maintenance_calories and total_kcal < target_kcal:
            st.info("🔄 Статус: Ты на уровне удержания веса. Хорошо, но для мощного роста нужен профицит!")
        else:
            st.success("🔥 Статус: ИДЕАЛЬНАЯ АНАБОЛИЧЕСКАЯ ЗОНА! Вес и мышцы прут вверх! Так держать!")

        # Полосы выполнения плана
        st.write(f"🔥 Калории: {round(total_kcal)} / {round(target_kcal)} ккал")
        st.progress(min(max(total_kcal / target_kcal, 0.0), 1.0))
        
        st.write(f"🍗 Белки: {round(total_p, 1)} / {round(target_p)} г")
        st.progress(min(max(total_p / target_p, 0.0), 1.0))
        
        st.write(f"🥑 Жиры: {round(total_f, 1)} / {round(target_f)} г")
        st.progress(min(max(total_f / target_f, 0.0), 1.0))
        
        st.write(f"🍞 Углеводы: {round(total_c, 1)} / {round(target_c)} г")
        st.progress(min(max(total_c / target_c, 0.0), 1.0))
        
        # Добиваем текст для экспорта результатов
        export_text += f"ИТОГО ЗА ДЕНЬ:\n🔥 Калории: {round(total_kcal)}/{round(target_kcal)} ккал\n🍗 Белки: {round(total_p)}г\n🥑 Жиры: {round(total_f)}г\n🍞 Углеводы: {round(total_c)}г\n💧 Вода: {st.session_state.water_intake}мл"
        
        st.markdown("---")
        # Фишка №2: Экспорт
        st.subheader("📲 Поделиться рационом")
        st.text_area("Скопируй этот текст и отправь тренеру в Telegram:", value=export_text, height=150)
        
        if st.button("Очистить Дневник Питания 🗑️", type="secondary"):
            st.session_state.meal_bag = []
            st.rerun()
    else:
        st.info("Твой дневник питания пуст. Начни наполнять его с левой панели!")