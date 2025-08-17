import streamlit as st
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates
import numpy as np
import math

# Убедитесь, что файл vehicle_constructor.py находится в той же папке
from vehicle_constructor import ParametricVehicle 

# --- Вспомогательные функции ---
def calculate_pixel_distance(p1, p2):
    """Рассчитывает евклидово расстояние между двумя точками в пикселях."""
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

# --- Инициализация состояния ---
if "points" not in st.session_state:
    st.session_state["points"] = []
if "pixels_per_meter" not in st.session_state:
    st.session_state["pixels_per_meter"] = None

# --- Основное приложение Streamlit ---
st.set_page_config(layout="wide")
st.title("Движок-Конструктор 3D-моделей (Этап 2)")

# --- Боковая панель для управления ---
st.sidebar.header("Управление")
uploaded_file = st.sidebar.file_uploader("Загрузите чертеж (PNG, JPG)", type=["png", "jpg", "jpeg"])

if st.sidebar.button("Сбросить точки"):
    st.session_state["points"] = []
    st.session_state["pixels_per_meter"] = None
    st.rerun()

st.sidebar.info("Кликните на чертеж, чтобы отметить ключевые точки.")

# --- Секция калибровки в боковой панели ---
# Эта секция теперь будет обновляться корректно
with st.sidebar:
    st.header("Калибровка масштаба")
    if len(st.session_state.points) >= 2:
        st.markdown("Отметьте 2 точки для известного размера.")
        
        reference_dimension_type = st.selectbox(
            "Что измеряют первые 2 точки?",
            ("Колесная база", "Диаметр колеса", "Длина полуприцепа")
        )
        
        real_size_m = st.number_input(
            f"Введите реальный размер для '{reference_dimension_type}' (в метрах)",
            min_value=0.1, value=3.8, step=0.1
        )

        if st.button("Рассчитать масштаб"):
            p1 = st.session_state.points[0]
            p2 = st.session_state.points[1]
            pixel_dist = calculate_pixel_distance(p1, p2)
            
            if pixel_dist > 0:
                st.session_state.pixels_per_meter = pixel_dist / real_size_m
                # st.rerun() здесь не нужен, Streamlit сам обновит значение
            else:
                st.error("Расстояние между точками равно нулю.")
    else:
        st.warning("Отметьте как минимум 2 точки для калибровки.")

    # Отображаем рассчитанный масштаб
    if st.session_state.pixels_per_meter:
        st.success(f"Масштаб: {st.session_state.pixels_per_meter:.2f} пикс/метр")
    else:
        st.info("Масштаб не рассчитан.")


# --- Основная область ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("2D Чертеж")
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        image_with_points = image.copy()
        draw = ImageDraw.Draw(image_with_points)
        
        for i, point in enumerate(st.session_state.points):
            x, y = point
            radius = 5
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill="red", outline="red")
            draw.text((x + radius, y), str(i + 1), fill="black")

        value = streamlit_image_coordinates(image_with_points, key="local")

        if value:
            point = value["x"], value["y"]
            if point not in st.session_state.points:
                st.session_state.points.append(point)
                # УБРАН ЛИШНИЙ st.rerun() - ЭТО БЫЛО ПРИЧИНОЙ ОШИБКИ
                st.experimental_rerun()


    else:
        st.info("Пожалуйста, загрузите изображение чертежа в боковой панели.")
    
    st.write("Отмеченные точки (в пикселях):")
    if st.session_state.points:
        st.write(st.session_state.points)


with col2:
    st.subheader("3D Модель")
    
    # TODO: На следующем шаге здесь будет создаваться модель с рассчитанными параметрами
    default_truck = ParametricVehicle()
    fig = default_truck.generate_figure()
    st.plotly_chart(fig, use_container_width=True)
