import streamlit as st
import difflib
from foods import FOOD_DATABASE

# Настройки страницы
st.set_page_config(page_title="Масса-Ультра Калькулятор", page_icon="🏋️‍♂️", layout="wide")

# Инициализация сессии для тарелки
if "meal_bag" not in st.session_state:
    st.session_state.meal_bag = []

st.title("🏋️‍♂️ Калькулятор Набора Массы & Гастро-СНГ Кухня")
st.write("Считай КБЖУ национальных блюд СНГ и спортивных продуктов с умным трекером калорий.")

# --- БОКОВАЯ ПАНЕЛЬ: Фишка от себя (Расчет профицита) ---
st.sidebar.header("🎯 Твоя цель на массу")
user_weight = st.sidebar.number_input("Твой вес (кг):", min_value=40, max_value=160, value=70)
activity_level = st.sidebar.selectbox("Уровень тренировок:", [
    "3 тренировки в неделю", 
    "4-5 тренировок в неделю", 
    "Хардкорный ежедневный кач"
])

# Простая, но эффективная формула для профицита набора массы
base_calories = user_weight * 33 # Поддержание
if activity_level == "3 тренировки в неделю":
    target_kcal = base_calories + 400
elif activity_level == "4-5 тренировок в неделю":
    target_kcal = base_calories + 600
else:
    target_kcal = base_calories + 800

# Расчет макросов на массу (Белок 2г/кг, Жиры 1г/кг, остальное угли)
target_p = user_weight * 2.0
target_f = user_weight * 1.0
target_c = (target_kcal - (target_p * 4) - (target_f * 9)) / 4

st.sidebar.markdown(f"""
**Рекомендуемая норма для роста:**
* 🔥 Калории: **{round(target_kcal)} ккал**
* 🍗 Белки: **{round(target_p)} г**
* 🥑 Жиры: **{round(target_f)} г**
* 🍞 Углеводы: **{round(target_c)} г**
""")

# --- ОСНОВНОЙ ИНТЕРФЕЙС ---
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🔍 Поиск и добавление продуктов")
    search_input = st.text_input("Введите блюдо или ингредиент (например: бешбармак, конина, плов, прот):").lower().strip()

    if search_input:
        filtered_foods = [food for food in FOOD_DATABASE.keys() if search_input in food.lower()]
        if not filtered_foods:
            filtered_foods = difflib.get_close_matches(search_input, FOOD_DATABASE.keys(), n=3, cutoff=0.5)
    else:
        filtered_foods = list(FOOD_DATABASE.keys())

    if filtered_foods:
        selected_product = st.selectbox("Выберите из списка найденных:", filtered_foods)
        unit = FOOD_DATABASE[selected_product]["unit"]
        amount = st.number_input(f"Количество ({unit}):", min_value=1, max_value=2000, value=150, step=10)
        
        if st.button("Добавить в тарелку ➕", use_container_width=True):
            nutrients = FOOD_DATABASE[selected_product]
            ratio = amount / 100.0
            
            st.session_state.meal_bag.append({
                "name": selected_product,
                "amount": amount,
                "unit": unit,
                "kcal": nutrients["калории"] * ratio,
                "p": nutrients["белки"] * ratio,
                "f": nutrients["жиры"] * ratio,
                "c": nutrients["углеводы"] * ratio
            })
            st.success(f"Добавлено: {selected_product}")
    else:
        st.error("⚠️ Ничего не найдено. Напиши точнее (например: 'казы', 'плов', 'шашлык').")

with col_right:
    st.subheader("📥 Содержимое твоей тарелки")
    
    if st.session_state.meal_bag:
        total_kcal = total_p = total_f = total_c = 0
        
        for item in st.session_state.meal_bag:
            total_kcal += item["kcal"]
            total_p += item["p"]
            total_f += item["f"]
            total_c += item["c"]
            
            st.write(f"▪️ **{item['name']}** — {item['amount']} {item['unit']} | {round(item['kcal'])} ккал")
        
        st.markdown("---")
        st.markdown("### 📊 ИТОГО И ВЫПОЛНЕНИЕ ПЛАНА:")
        
        # Показываем прогресс бары относительно целей из сайдбара
        st.write(f"🔥 Калории: {round(total_kcal)} / {round(target_kcal)} ккал")
        st.progress(min(total_kcal / target_kcal, 1.0))
        
        st.write(f"🍗 Белки: {round(total_p, 1)} / {round(target_p)} г")
        st.progress(min(total_p / target_p, 1.0))
        
        st.write(f"🥑 Жиры: {round(total_f, 1)} / {round(target_f)} г")
        st.progress(min(total_f / target_f, 1.0))
        
        st.write(f"🍞 Углеводы: {round(total_c, 1)} / {round(target_c)} г")
        st.progress(min(total_c / target_c, 1.0))
        
        if st.button("Очистить тарелку 🗑️", type="secondary"):
            st.session_state.meal_bag = []
            st.rerun()
    else:
        st.info("Твоя тарелка пока пуста. Начни добавлять еду слева!")