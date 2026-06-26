import streamlit as st
import difflib
from foods import FOOD_DATABASE  # Импортируем нашу базу продуктов

# Устанавливаем настройки страницы
st.set_page_config(page_title="Масса-Калькулятор КБЖУ", page_icon="💪", layout="centered")

# Инициализация сессии для хранения добавленных продуктов
if "meal_bag" not in st.session_state:
    st.session_state.meal_bag = []

st.title("💪 Калькулятор «Чистого Набора Массы»")
st.write("Сайт-калькулятор анаболической корзины. Ищите культовые продукты и собирайте свой идеальный рацион.")

# --- Блок интерфейса: Умный поиск ---
st.subheader("🔍 Поиск и добавление продуктов")

# Текстовое поле для ввода ключевого слова
search_input = st.text_input("Введите ключевое слово (например: курица, молоко, рис, прот):").lower().strip()

# Фильтрация базы данных по ключевому слову
if search_input:
    # 1. Ищем прямое вхождение букв (например, "кури" в "куриное филе")
    filtered_foods = [food for food in FOOD_DATABASE.keys() if search_input in food.lower()]
    
    # 2. Если прямого вхождения нет, аккуратно проверяем на опечатки, но строго (cutoff=0.6)
    if not filtered_foods:
        filtered_foods = difflib.get_close_matches(search_input, FOOD_DATABASE.keys(), n=3, cutoff=0.6)
else:
    filtered_foods = list(FOOD_DATABASE.keys())

# Выпадающий список с отфильтрованными продуктами
if filtered_foods:
    selected_product = st.selectbox("Выберите продукт из найденных:", filtered_foods)
    
    # Динамически меняем текст (г или мл) в зависимости от выбранного продукта
    unit = FOOD_DATABASE[selected_product]["unit"]
    
    # Ввод объема / веса
    amount = st.number_input(f"Укажите количество ({unit}):", min_value=1, max_value=2000, value=100, step=10)
    
    # Кнопка добавления в рацион
    if st.button("Добавить в тарелку ➕", use_container_width=True):
        nutrients = FOOD_DATABASE[selected_product]
        ratio = amount / 100.0
        
        # Добавляем позицию
        st.session_state.meal_bag.append({
            "name": selected_product,
            "amount": amount,
            "unit": unit,
            "kcal": nutrients["калории"] * ratio,
            "p": nutrients["белки"] * ratio,
            "f": nutrients["жиры"] * ratio,
            "c": nutrients["углеводы"] * ratio
        })
        st.success(f"Добавлено: {selected_product} ({amount} {unit})")
else:
    st.error("⚠️ Такой продукт не найден в анаболической базе данных. Попробуйте ввести другое слово.")

st.markdown("---")

# --- Блок интерфейса: Ваша Анаболическая Тарелка ---
st.subheader("📥 Ваша текущая корзина питания")

if st.session_state.meal_bag:
    total_kcal = total_p = total_f = total_c = 0
    
    # Отображаем список красивыми строками
    for idx, item in enumerate(st.session_state.meal_bag):
        total_kcal += item["kcal"]
        total_p += item["p"]
        total_f += item["f"]
        total_c += item["c"]
        
        st.write(f"▪️ **{item['name']}** — {item['amount']} {item['unit']} | "
                 f"🔥 {round(item['kcal'])} ккал | Б: {round(item['p'], 1)}г | Ж: {round(item['f'], 1)}г | У: {round(item['c'], 1)}г")
    
    st.markdown("---")
    
    # Итоговые карточки (Метрики)
    st.markdown("### 📊 ИТОГО ЗА ПРИЕМ ПИЩИ:")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="Калории", value=f"{round(total_kcal)} ккал")
    with col2:
        st.metric(label="Белки (🍗)", value=f"{round(total_p, 1)} г")
    with col3:
        st.metric(label="Жиры (🥑)", value=f"{round(total_f, 1)} г")
    with col4:
        st.metric(label="Углеводы (🍞)", value=f"{round(total_c, 1)} г")
        
    # Кнопка сброса
    if st.button("Очистить корзину 🗑️", type="secondary"):
        st.session_state.meal_bag = []
        st.st.rerun()
else:
    st.info("Корзина пуста. Добавьте продукты выше, чтобы рассчитать общую сумму.")