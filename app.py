import streamlit as st
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates
import numpy as np
import math

# Убедитесь, что файл vehicle_constructor.py находится в той же папке
from vehicle_constructor import ParametricVehicle 

# --- Вспомогательные функции ---
def calculate_pixel_distance(p1, p2, axis='x'):
    """Рассчитывает расстояние между двумя точками по выбранной оси."""
    if axis == 'x':
        return abs(p2[0] - p1[0])
    elif axis == 'y':
        return abs(p2[1] - p1[1])
    # Евклидово расстояние для диагоналей
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

# --- Инициализация состояния ---
if "points" not in st.session_state:
    st.session_state["points"] = []
if "pixels_per_meter" not in st.session_state:
    st.session_state["pixels_per_meter"] = None
if "vehicle_params" not in st.session_state:
    st.session_state["vehicle_params"] = {}

# --- Основное приложение Streamlit ---
st.set_page_config(layout="wide")
st.title("Движок-Конструктор 3D-моделей (Этап 2)")

# --- Боковая панель для управления ---
st.sidebar.header("Управление")
uploaded_file = st.sidebar.file_uploader("Загрузите чертеж (PNG, JPG)", type=["png", "jpg", "jpeg"])

if st.sidebar.button("Сбросить точки"):
    st.session_state["points"] = []
    st.session_state["pixels_per_meter"] = None
    st.session_state["vehicle_params"] = {}
    st.rerun()

st.sidebar.info("Кликните на чертеж, чтобы отметить ключевые точки.")

# --- Секция калибровки в боковой панели ---
with st.sidebar:
    st.header("1. Калибровка масштаба")
    if len(st.session_state.points) >= 2:
        st.markdown("Точки **1** и **2** используются для калибровки.")
        
        real_size_m = st.number_input(
            f"Введите реальное расстояние между точками 1 и 2 (в метрах)",
            min_value=0.1, value=3.8, step=0.1, key="real_size_input"
        )

        if st.button("Рассчитать масштаб"):
            p1 = st.session_state.points[0]
            p2 = st.session_state.points[1]
            pixel_dist = calculate_pixel_distance(p1, p2, axis='x')
            
            if pixel_dist > 0:
                st.session_state.pixels_per_meter = pixel_dist / real_size_m
            else:
                st.error("Расстояние между точками равно нулю.")
    else:
        st.warning("Отметьте как минимум 2 точки для калибровки.")

    if st.session_state.pixels_per_meter:
        st.success(f"Масштаб: {st.session_state.pixels_per_meter:.2f} пикс/метр")
    else:
        st.info("Масштаб не рассчитан.")

    # --- Секция перестроения 3D-модели ---
    st.header("2. Расчет параметров")
    st.markdown("""
    **Схема расстановки точек:**
    - **1, 2**: Центры передней и задней оси тягача.
    - **3, 4**: Передний и задний край полуприцепа.
    - **5, 6**: Верхний и нижний край полуприцепа.
    - **7**: Передний край (бампер) тягача.
    """)
    if st.session_state.pixels_per_meter and len(st.session_state.points) >= 7:
        st.markdown("**Введите недостающие размеры (ширину):**")
        cab_width_m = st.number_input("Ширина кабины (м)", min_value=0.1, value=2.5, step=0.05)
        trailer_width_m = st.number_input("Ширина полуприцепа (м)", min_value=0.1, value=2.55, step=0.05)

        if st.button("Перестроить 3D модель"):
            ppm = st.session_state.pixels_per_meter
            pts = st.session_state.points
            
            params = {
                'wheelbase': calculate_pixel_distance(pts[0], pts[1], axis='x') / ppm,
                'trailer_length': calculate_pixel_distance(pts[2], pts[3], axis='x') / ppm,
                'trailer_height': calculate_pixel_distance(pts[4], pts[5], axis='y') / ppm,
                'cab_length': calculate_pixel_distance(pts[6], pts[0], axis='x') / ppm,
                # --- ИСПРАВЛЕНИЕ: Добавлено деление на ppm ---
                'wheel_diameter': (calculate_pixel_distance(pts[4], pts[5], axis='y') / ppm) * 0.4,
                'cab_width': cab_width_m,
                'trailer_width': trailer_width_m
            }
            st.session_state.vehicle_params = params
            st.success("Параметры рассчитаны!")
            st.write(params)
    else:
        st.warning("Рассчитайте масштаб и отметьте минимум 7 точек.")


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
                st.rerun()
    else:
        st.info("Пожалуйста, загрузите изображение чертежа в боковой панели.")
    
    st.write("Отмеченные точки (в пикселях):")
    if st.session_state.points:
        st.write(st.session_state.points)

with col2:
    st.subheader("3D Модель")
    
    if st.session_state.vehicle_params:
        vp = st.session_state.vehicle_params
        truck = ParametricVehicle(
            wheelbase=vp.get('wheelbase', 3.8),
            trailer_length=vp.get('trailer_length', 13.6),
            trailer_height=vp.get('trailer_height', 2.7),
            cab_length=vp.get('cab_length', 2.2),
            wheel_diameter=vp.get('wheel_diameter', 1.0),
            cab_width=vp.get('cab_width', 2.5),
            trailer_width=vp.get('trailer_width', 2.55)
        )
    else:
        truck = ParametricVehicle()

    fig = truck.generate_figure()
    st.plotly_chart(fig, use_container_width=True)

