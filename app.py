import streamlit as st
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates
import numpy as np

# Убедитесь, что файл vehicle_constructor.py находится в той же папке
from vehicle_constructor import ParametricVehicle 

# --- Инициализация состояния ---
if "points" not in st.session_state:
    st.session_state["points"] = []

# --- Основное приложение Streamlit ---
st.set_page_config(layout="wide")
st.title("Движок-Конструктор 3D-моделей (Этап 2)")

# --- Боковая панель для управления ---
st.sidebar.header("Управление")
uploaded_file = st.sidebar.file_uploader("Загрузите чертеж (PNG, JPG)", type=["png", "jpg", "jpeg"])

if st.sidebar.button("Сбросить точки"):
    st.session_state["points"] = []

st.sidebar.info("Кликните на чертеж, чтобы отметить ключевые точки.")

# --- Основная область ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("2D Чертеж")
    if uploaded_file is not None:
        image = Image.open(uploaded_file)

        # --- НОВЫЙ КОМПОНЕНТ ДЛЯ ПОЛУЧЕНИЯ КООРДИНАТ ---
        value = streamlit_image_coordinates(image, key="local")

        # Если пользователь кликнул, value будет содержать координаты
        if value:
            point = value["x"], value["y"]
            # Добавляем точку в список, если ее там еще нет
            if point not in st.session_state["points"]:
                st.session_state["points"].append(point)
    
    else:
        st.info("Пожалуйста, загрузите изображение чертежа в боковой панели.")
    
    st.write("Отмеченные точки (в пикселях):")
    # Отображаем точки в более простом виде
    if st.session_state["points"]:
        st.write(st.session_state["points"])


with col2:
    st.subheader("3D Модель")
    
    default_truck = ParametricVehicle()
    fig = default_truck.generate_figure()
    st.plotly_chart(fig, use_container_width=True)

