import streamlit as st
from PIL import Image, ImageDraw
from streamlit_image_coordinates import streamlit_image_coordinates
import math

# Убедитесь, что файл vehicle_constructor.py находится в той же папке
from vehicle_constructor import Tractor, SemiTrailer, Van, Scene

# --- Вспомогательные функции ---
def calculate_pixel_distance(p1, p2, axis='x'):
    """Рассчитывает расстояние между двумя точками по выбранной оси."""
    if axis == 'x': return abs(p2[0] - p1[0])
    if axis == 'y': return abs(p2[1] - p1[1])
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

# --- Инициализация состояния ---
def init_session_state():
    defaults = {
        "points": [],
        "pixels_per_meter": None,
        "vehicle_type": "Сборка автопоезда",
        "library": {},
        "tractor_obj": None,
        "trailer_obj": None,
        "van_obj": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Сброс состояния при смене режима ---
def on_vehicle_type_change():
    st.session_state.points = []
    st.session_state.pixels_per_meter = None

# --- Основное приложение ---
st.set_page_config(layout="wide")
st.title("Движок-Конструктор 3D-моделей")

# --- Боковая панель ---
st.sidebar.header("Управление")

vehicle_type = st.sidebar.selectbox(
    "Выберите режим",
    ("Сборка автопоезда", "Тягач", "Прицеп", "Фургон"),
    key="vehicle_type",
    on_change=on_vehicle_type_change
)

# --- Динамический интерфейс в боковой панели ---

# --- ИНТЕРФЕЙС ДЛЯ СБОРКИ ---
if vehicle_type == "Сборка автопоезда":
    st.sidebar.header("Сборка")
    tractors = {name: obj for name, obj in st.session_state.library.items() if isinstance(obj, Tractor)}
    trailers = {name: obj for name, obj in st.session_state.library.items() if isinstance(obj, SemiTrailer)}
    if not tractors or not trailers:
        st.sidebar.warning("Сначала создайте и сохраните в библиотеку хотя бы один тягач и один прицеп.")
    else:
        sel_tractor_name = st.sidebar.selectbox("Выберите тягач", list(tractors.keys()))
        sel_trailer_name = st.sidebar.selectbox("Выберите прицеп", list(trailers.keys()))
        if st.sidebar.button("Собрать автопоезд"):
            st.session_state.tractor_obj = tractors[sel_tractor_name]
            st.session_state.trailer_obj = trailers[sel_trailer_name]
            st.sidebar.success("Автопоезд готов к отображению!")

# --- ИНТЕРФЕЙСЫ ДЛЯ СОЗДАНИЯ ---
else:
    uploaded_file = st.sidebar.file_uploader("Загрузите чертеж", type=["png", "jpg", "jpeg"])
    
    if st.sidebar.button("Сбросить точки"):
        st.session_state.points = []
        st.rerun()

    if st.sidebar.button("Удалить последнюю точку"):
        if st.session_state.points:
            st.session_state.points.pop()
            st.rerun()
    
    st.sidebar.info("Кликните на чертеж, чтобы отметить ключевые точки.")
    st.sidebar.header("1. Калибровка масштаба")
    if len(st.session_state.points) >= 2:
        real_size_m = st.number_input("Реальное расстояние м/у точками 1 и 2 (м)", min_value=0.1, value=3.8, step=0.1)
        if st.button("Рассчитать масштаб"):
            p1, p2 = st.session_state.points[0], st.session_state.points[1]
            pixel_dist = calculate_pixel_distance(p1, p2)
            st.session_state.pixels_per_meter = pixel_dist / real_size_m if pixel_dist > 0 else 0
    
    if st.session_state.pixels_per_meter:
        st.success(f"Масштаб: {st.session_state.pixels_per_meter:.2f} пикс/метр")

    # --- ИНТЕРФЕЙС ДЛЯ ТЯГАЧА ---
    if vehicle_type == "Тягач":
        st.sidebar.header("2. Параметры тягача")
        st.sidebar.markdown("""
        - **1, 2**: Колесная база (центры осей).
        - **3**: Передний край (бампер).
        - **4**: Задний край кабины.
        - **5**: Центр седла.
        - **6, 7**: Верх/низ колеса.
        """)
        MIN_POINTS = 7
        if st.session_state.pixels_per_meter and len(st.session_state.points) >= MIN_POINTS:
            brand = st.sidebar.text_input("Марка", "Scania")
            model = st.sidebar.text_input("Модель", "R450")
            cab_width_m = st.sidebar.number_input("Ширина кабины (м)", 0.1, value=2.5, step=0.05)
            num_tr = st.sidebar.number_input("Кол-во задних осей", 1, value=2, step=1)
            sp_tr = st.sidebar.number_input("Расст. между осями (м)", 0.1, value=1.3, step=0.1)
            wheel_type = st.sidebar.selectbox("Тип задних колес", ('dual', 'single'))

            if st.sidebar.button("Перестроить и Сохранить"):
                ppm = st.session_state.pixels_per_meter
                pts = st.session_state.points
                params = {'brand': brand, 'model': model, 'front_axle_pos': calculate_pixel_distance(pts[2], pts[0])/ppm, 'wheelbase': calculate_pixel_distance(pts[0], pts[1])/ppm, 'cab_length': calculate_pixel_distance(pts[2], pts[3])/ppm, 'saddle_pos_from_rear_axle': calculate_pixel_distance(pts[1], pts[4])/ppm, 'wheel_diameter': calculate_pixel_distance(pts[5], pts[6], 'y')/ppm, 'cab_width': cab_width_m, 'num_rear_axles': num_tr, 'rear_axle_spacing': sp_tr, 'wheel_type': wheel_type}
                
                new_tractor = Tractor(**params)
                unique_name = new_tractor.get_unique_name()
                st.session_state.library[unique_name] = new_tractor
                st.session_state.tractor_obj = new_tractor
                st.sidebar.success(f"Тягач '{unique_name}' сохранен!")

    # --- ИНТЕРФЕЙС ДЛЯ ПРИЦЕПА ---
    elif vehicle_type == "Прицеп":
        st.sidebar.header("2. Параметры прицепа")
        st.sidebar.markdown("""
        - **1, 2**: Расстояние между центрами первой и последней оси.
        - **3, 4**: Передний и задний край.
        - **5, 6**: Верхний и нижний край.
        - **7**: Центр шкворня.
        """)
        MIN_POINTS = 7
        if st.session_state.pixels_per_meter and len(st.session_state.points) >= MIN_POINTS:
            brand = st.sidebar.text_input("Марка", "Schmitz")
            model = st.sidebar.text_input("Модель", "Cargobull")
            trl_w = st.sidebar.number_input("Ширина (м)", 0.1, value=2.55, step=0.05)
            num_trl = st.sidebar.number_input("Кол-во осей", 1, value=3, step=1)

            if st.sidebar.button("Перестроить и Сохранить"):
                ppm = st.session_state.pixels_per_meter
                pts = st.session_state.points
                axle_spacing = calculate_pixel_distance(pts[0], pts[1]) / (num_trl - 1) / ppm if num_trl > 1 else 0
                params = {'brand': brand, 'model': model, 'length': calculate_pixel_distance(pts[2], pts[3])/ppm, 'height': calculate_pixel_distance(pts[4], pts[5], 'y')/ppm, 'kingpin_offset': calculate_pixel_distance(pts[2], pts[6])/ppm, 'axle_pos_from_rear': calculate_pixel_distance(pts[1], pts[3])/ppm, 'wheel_diameter': calculate_pixel_distance(pts[4], pts[5], 'y')*0.4/ppm, 'width': trl_w, 'num_axles': num_trl, 'axle_spacing': axle_spacing}
                
                new_trailer = SemiTrailer(**params)
                unique_name = new_trailer.get_unique_name()
                st.session_state.library[unique_name] = new_trailer
                st.session_state.trailer_obj = new_trailer
                st.sidebar.success(f"Прицеп '{unique_name}' сохранен!")

# --- Основная область ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("2D Чертеж")
    if vehicle_type != "Сборка автопоезда" and 'uploaded_file' in locals() and uploaded_file:
        image = Image.open(uploaded_file)
        image_with_points = image.copy()
        draw = ImageDraw.Draw(image_with_points)
        
        for i, point in enumerate(st.session_state.points):
            x, y = point; radius = 5
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill="red", outline="red")
            draw.text((x + radius, y), str(i + 1), fill="black")

        value = streamlit_image_coordinates(image_with_points, key="local")

        if value:
            point = value["x"], value["y"]
            if point not in st.session_state.points:
                st.session_state.points.append(point)
                st.rerun()
    else:
        st.info("Выберите режим или компоненты из библиотеки.")
    
    st.write("Отмеченные точки:")
    st.json(st.session_state.points)

with col2:
    st.subheader("3D Модель")
    scene = Scene()
    if st.session_state.vehicle_type == "Сборка автопоезда":
        if st.session_state.tractor_obj and st.session_state.trailer_obj:
            scene.add_articulated_vehicle(st.session_state.tractor_obj, st.session_state.trailer_obj)
    elif st.session_state.vehicle_type == "Тягач" and st.session_state.tractor_obj:
        scene.add(st.session_state.tractor_obj)
    elif st.session_state.vehicle_type == "Прицеп" and st.session_state.trailer_obj:
        scene.add(st.session_state.trailer_obj)
    elif st.session_state.vehicle_type == "Фургон" and st.session_state.van_obj:
        scene.add(st.session_state.van_obj)
    
    fig = scene.generate_figure()
    st.plotly_chart(fig, use_container_width=True)

st.sidebar.header("Библиотека")
if st.session_state.library:
    st.sidebar.json(list(st.session_state.library.keys()))
else:
    st.sidebar.write("Пусто")

