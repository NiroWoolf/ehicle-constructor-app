import streamlit as st
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates
import numpy as np
import math

# Убедитесь, что файл vehicle_constructor.py находится в той же папке
from vehicle_constructor import Tractor, SemiTrailer, Van, Scene

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
if "vehicle_type" not in st.session_state:
    st.session_state["vehicle_type"] = "Автопоезд"
if "scene" not in st.session_state:
    st.session_state["scene"] = Scene()
    st.session_state.scene.add_articulated_vehicle(Tractor(), SemiTrailer())


# --- Основное приложение Streamlit ---
st.set_page_config(layout="wide")
st.title("Движок-Конструктор 3D-моделей")

# --- Боковая панель для управления ---
st.sidebar.header("Управление")

# --- ГЛАВНОЕ МЕНЮ ВЫБОРА ---
vehicle_type = st.sidebar.selectbox(
    "Выберите тип для отрисовки",
    ("Автопоезд", "Фургон", "Только тягач", "Только полуприцеп"),
    key="vehicle_type_selector"
)
st.session_state.vehicle_type = vehicle_type


uploaded_file = st.sidebar.file_uploader("Загрузите чертеж (PNG, JPG)", type=["png", "jpg", "jpeg"])

if st.sidebar.button("Сбросить все"):
    st.session_state.clear()
    st.rerun()

if st.sidebar.button("Удалить последнюю точку"):
    if st.session_state.points:
        st.session_state.points.pop()
        st.rerun()

st.sidebar.info("Кликните на чертеж, чтобы отметить ключевые точки.")

with st.sidebar:
    st.header("1. Калибровка масштаба")
    # ... (код калибровки остается прежним, но мы его пока скроем, если не выбран автопоезд)

    # --- ДИНАМИЧЕСКИЙ ИНТЕРФЕЙС ---
    
    # --- ИНТЕРФЕЙС ДЛЯ АВТОПОЕЗДА ---
    if st.session_state.vehicle_type == "Автопоезд":
        st.header("Параметры автопоезда")
        st.markdown("""
        **Схема расстановки точек (Автопоезд):**
        - **1, 2**: Центры передней и **первой задней** оси тягача.
        - **3**: Передний край (бампер) тягача.
        - **4**: Задний край кабины.
        - **5**: Центр **точки сцепки** (седло/шкворень).
        - **6, 7**: Передний и задний край полуприцепа.
        - **8, 9**: Верхний и нижний край полуприцепа.
        - **10**: Центр **первой** оси полуприцепа.
        """)
        MIN_POINTS = 10
        if st.session_state.pixels_per_meter and len(st.session_state.points) >= MIN_POINTS:
            with st.expander("Параметры тягача", expanded=True):
                cab_width_m = st.number_input("Ширина кабины (м)", 0.1, value=2.5, step=0.05, key="ac_cab_w")
                num_tr = st.number_input("Кол-во задних осей тягача", 1, value=2, step=1, key="ac_tr_ax_num")
                sp_tr = st.number_input("Расст. между осями тягача (м)", 0.1, value=1.3, step=0.1, key="ac_tr_ax_sp")
            with st.expander("Параметры полуприцепа", expanded=True):
                trl_w = st.number_input("Ширина полуприцепа (м)", 0.1, value=2.55, step=0.05, key="ac_trl_w")
                num_trl = st.number_input("Кол-во осей полуприцепа", 1, value=3, step=1, key="ac_trl_ax_num")
                sp_trl = st.number_input("Расст. между осями полуприцепа (м)", 0.1, value=1.3, step=0.1, key="ac_trl_ax_sp")
            
            if st.button("Перестроить Автопоезд"):
                ppm = st.session_state.pixels_per_meter
                pts = st.session_state.points
                
                tractor_p = {'front_axle_pos': calculate_pixel_distance(pts[2], pts[0])/ppm, 'wheelbase': calculate_pixel_distance(pts[0], pts[1])/ppm, 'cab_length': calculate_pixel_distance(pts[2], pts[3])/ppm, 'saddle_pos_from_rear_axle': calculate_pixel_distance(pts[1], pts[4])/ppm, 'wheel_diameter': (calculate_pixel_distance(pts[7], pts[8], 'y')*0.4)/ppm, 'cab_width': cab_width_m, 'num_rear_axles': num_tr, 'rear_axle_spacing': sp_tr}
                trailer_p = {'length': calculate_pixel_distance(pts[5], pts[6])/ppm, 'height': calculate_pixel_distance(pts[7], pts[8], 'y')/ppm, 'kingpin_offset': calculate_pixel_distance(pts[5], pts[4])/ppm, 'axle_pos_from_rear': calculate_pixel_distance(pts[9], pts[6])/ppm, 'wheel_diameter': (calculate_pixel_distance(pts[7], pts[8], 'y')*0.4)/ppm, 'width': trl_w, 'num_axles': num_trl, 'axle_spacing': sp_trl}
                
                st.session_state.scene = Scene()
                st.session_state.scene.add_articulated_vehicle(Tractor(**tractor_p), SemiTrailer(**trailer_p))
                st.success("Модель перестроена!")

    # --- ИНТЕРФЕЙС ДЛЯ ФУРГОНА ---
    elif st.session_state.vehicle_type == "Фургон":
        st.header("Параметры фургона")
        st.markdown("""
        **Схема расстановки точек (Фургон):**
        - **1, 2**: Центры передней и **первой задней** оси.
        - **3**: Передний край (бампер).
        - **4**: Начало грузового отсека.
        - **5**: Конец грузового отсека.
        - **6, 7**: Верхний и нижний край грузового отсека.
        """)
        MIN_POINTS = 7
        if st.session_state.pixels_per_meter and len(st.session_state.points) >= MIN_POINTS:
            body_width_m = st.number_input("Ширина фургона (м)", 0.1, value=2.4, step=0.05, key="van_w")
            num_van_rear_axles = st.number_input("Кол-во задних осей", 1, value=1, step=1, key="van_ax_num")
            
            if st.button("Перестроить Фургон"):
                ppm = st.session_state.pixels_per_meter
                pts = st.session_state.points
                van_p = {'front_axle_pos': calculate_pixel_distance(pts[2], pts[0])/ppm, 'wheelbase': calculate_pixel_distance(pts[0], pts[1])/ppm, 'cab_length': calculate_pixel_distance(pts[2], pts[3])/ppm, 'body_length': calculate_pixel_distance(pts[3], pts[4])/ppm, 'body_height': calculate_pixel_distance(pts[5], pts[6], 'y')/ppm, 'wheel_diameter': (calculate_pixel_distance(pts[5], pts[6], 'y')*0.4)/ppm, 'body_width': body_width_m, 'num_rear_axles': num_van_rear_axles}
                
                st.session_state.scene = Scene()
                st.session_state.scene.add_van(Van(**van_p))
                st.success("Модель перестроена!")

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
    
    # Всегда отрисовываем текущую сцену
    fig = st.session_state.scene.generate_figure()
    st.plotly_chart(fig, use_container_width=True)
