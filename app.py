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
    st.session_state.clear()
    st.rerun()

if st.sidebar.button("Удалить последнюю точку"):
    if st.session_state.points:
        st.session_state.points.pop()
        st.rerun()

st.sidebar.info("Кликните на чертеж, чтобы отметить ключевые точки.")

with st.sidebar:
    st.header("1. Калибровка масштаба")
    if len(st.session_state.points) >= 2:
        st.markdown("Точки **1** и **2** используются для калибровки.")
        real_size_m = st.number_input(
            "Введите реальное расстояние между точками 1 и 2 (в метрах)",
            min_value=0.1, value=3.8, step=0.1, key="real_size_input"
        )
        if st.button("Рассчитать масштаб"):
            p1, p2 = st.session_state.points[0], st.session_state.points[1]
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

    st.header("2. Расчет параметров")
    # --- ИЗМЕНЕННАЯ СХЕМА ТОЧЕК ---
    st.markdown("""
    **Схема расстановки точек:**
    - **1, 2**: Центры передней и **первой задней** оси тягача (для калибровки).
    - **3**: Передний край (бампер) тягача.
    - **4**: Задний край кабины.
    - **5**: Центр **точки сцепки** (седло/шкворень).
    - **6, 7**: Передний и задний край полуприцепа.
    - **8, 9**: Верхний и нижний край полуприцепа.
    - **10**: Центр **первой** оси полуприцепа.
    """)
    MIN_POINTS_FOR_REBUILD = 10
    if st.session_state.pixels_per_meter and len(st.session_state.points) >= MIN_POINTS_FOR_REBUILD:
        st.markdown("**Введите недостающие параметры:**")
        cab_width_m = st.number_input("Ширина кабины (м)", min_value=0.1, value=2.5, step=0.05)
        trailer_width_m = st.number_input("Ширина полуприцепа (м)", min_value=0.1, value=2.55, step=0.05)
        
        st.markdown("**Конфигурация осей:**")
        num_tractor_rear_axles = st.number_input("Кол-во задних осей тягача", min_value=1, value=2, step=1)
        tractor_rear_axle_spacing = st.number_input("Расстояние между осями тягача (м)", min_value=0.1, value=1.3, step=0.1)
        num_trailer_axles = st.number_input("Кол-во осей полуприцепа", min_value=1, value=3, step=1)
        trailer_axle_spacing = st.number_input("Расстояние между осями полуприцепа (м)", min_value=0.1, value=1.3, step=0.1)
        
        if st.button("Перестроить 3D модель"):
            ppm = st.session_state.pixels_per_meter
            pts = st.session_state.points
            
            # --- ИСПРАВЛЕННАЯ ЛОГИКА РАСЧЕТОВ ---
            params = {
                'wheelbase': calculate_pixel_distance(pts[0], pts[1], axis='x') / ppm,
                'cab_length': calculate_pixel_distance(pts[2], pts[3], axis='x') / ppm,
                'saddle_position_from_rear_axle': calculate_pixel_distance(pts[1], pts[4], axis='x') / ppm,
                'trailer_length': calculate_pixel_distance(pts[5], pts[6], axis='x') / ppm,
                'kingpin_offset': calculate_pixel_distance(pts[5], pts[4], axis='x') / ppm,
                'trailer_height': calculate_pixel_distance(pts[7], pts[8], axis='y') / ppm,
                'trailer_axle_position_from_rear': calculate_pixel_distance(pts[9], pts[6], axis='x') / ppm,
                'wheel_diameter': (calculate_pixel_distance(pts[7], pts[8], axis='y') * 0.4) / ppm,
                'cab_width': cab_width_m,
                'trailer_width': trailer_width_m,
                'num_tractor_rear_axles': num_tractor_rear_axles,
                'tractor_rear_axle_spacing': tractor_rear_axle_spacing,
                'num_trailer_axles': num_trailer_axles,
                'trailer_axle_spacing': trailer_axle_spacing
            }
            st.session_state.vehicle_params = params
            st.success("Параметры рассчитаны!")
            st.write(params)
    else:
        st.warning(f"Рассчитайте масштаб и отметьте минимум {MIN_POINTS_FOR_REBUILD} точек.")

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
    
    truck = ParametricVehicle(**st.session_state.get("vehicle_params", {}))
    fig = truck.generate_figure()
    st.plotly_chart(fig, use_container_width=True)
