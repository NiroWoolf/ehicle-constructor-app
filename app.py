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
def init_state():
    if "points" not in st.session_state: st.session_state["points"] = []
    if "pixels_per_meter" not in st.session_state: st.session_state["pixels_per_meter"] = None
    if "vehicle_type" not in st.session_state: st.session_state["vehicle_type"] = "Автопоезд"
    if "library" not in st.session_state: st.session_state["library"] = {}

init_state()

# --- Основное приложение Streamlit ---
st.set_page_config(layout="wide")
st.title("Движок-Конструктор 3D-моделей")

# --- Боковая панель ---
st.sidebar.header("Управление")

vehicle_type = st.sidebar.selectbox(
    "Выберите режим",
    ("Сборка автопоезда", "Создать тягач", "Создать прицеп", "Создать фургон"),
    key="vehicle_type_selector"
)

uploaded_file = st.sidebar.file_uploader("Загрузите чертеж (PNG, JPG)", type=["png", "jpg", "jpeg"])

if st.sidebar.button("Сбросить точки"):
    st.session_state.points = []
    st.session_state.pixels_per_meter = None
    st.rerun()

if st.sidebar.button("Удалить последнюю точку"):
    if st.session_state.points:
        st.session_state.points.pop()
        st.rerun()

# --- Динамический интерфейс в боковой панели ---
with st.sidebar:
    
    # --- ИНТЕРФЕЙС СОЗДАНИЯ (ОБЩИЙ ДЛЯ ТЯГАЧА, ПРИЦЕПА, ФУРГОНА) ---
    if vehicle_type != "Сборка автопоезда":
        st.info("Кликните на чертеж, чтобы отметить ключевые точки.")
        st.header("1. Калибровка масштаба")
        if len(st.session_state.points) >= 2:
            real_size_m = st.number_input("Реальное расстояние м/у точками 1 и 2 (м)", min_value=0.1, value=3.8, step=0.1)
            if st.button("Рассчитать масштаб"):
                p1, p2 = st.session_state.points[0], st.session_state.points[1]
                pixel_dist = calculate_pixel_distance(p1, p2, axis='x')
                st.session_state.pixels_per_meter = pixel_dist / real_size_m if pixel_dist > 0 else 0
        else:
            st.warning("Отметьте минимум 2 точки.")
        
        if st.session_state.pixels_per_meter:
            st.success(f"Масштаб: {st.session_state.pixels_per_meter:.2f} пикс/метр")

    # --- ИНТЕРФЕЙС ДЛЯ ТЯГАЧА ---
    if vehicle_type == "Создать тягач":
        st.header("2. Параметры тягача")
        st.markdown("""
        - **1, 2**: Центры передней и первой задней оси.
        - **3**: Передний край (бампер).
        - **4**: Задний край кабины.
        - **5**: Центр седла.
        - **6, 7**: Верх/низ колеса.
        """)
        MIN_POINTS = 7
        if st.session_state.pixels_per_meter and len(st.session_state.points) >= MIN_POINTS:
            brand = st.text_input("Марка", "Scania")
            model = st.text_input("Модель", "R450")
            cab_width_m = st.number_input("Ширина кабины (м)", 0.1, value=2.5, step=0.05)
            num_tr = st.number_input("Кол-во задних осей", 1, value=2, step=1)
            sp_tr = st.number_input("Расст. между осями (м)", 0.1, value=1.3, step=0.1)
            wheel_type = st.selectbox("Тип задних колес", ('dual', 'single'))

            if st.button("Сохранить тягач в библиотеку"):
                ppm = st.session_state.pixels_per_meter
                pts = st.session_state.points
                params = {'brand': brand, 'model': model, 'front_axle_pos': calculate_pixel_distance(pts[2], pts[0])/ppm, 'wheelbase': calculate_pixel_distance(pts[0], pts[1])/ppm, 'cab_length': calculate_pixel_distance(pts[2], pts[3])/ppm, 'saddle_pos_from_rear_axle': calculate_pixel_distance(pts[1], pts[4])/ppm, 'wheel_diameter': calculate_pixel_distance(pts[5], pts[6], 'y')/ppm, 'cab_width': cab_width_m, 'num_rear_axles': num_tr, 'rear_axle_spacing': sp_tr, 'wheel_type': wheel_type}
                
                new_tractor = Tractor(**params)
                unique_name = new_tractor.get_unique_name()
                if unique_name in st.session_state.library:
                    st.error("Тягач с таким именем уже существует!")
                else:
                    st.session_state.library[unique_name] = new_tractor
                    st.success(f"Тягач '{unique_name}' сохранен!")

    # --- ИНТЕРФЕЙС ДЛЯ ПРИЦЕПА ---
    elif vehicle_type == "Создать прицеп":
        st.header("2. Параметры прицепа")
        st.markdown("""
        - **1, 2**: Центры первой и последней оси.
        - **3, 4**: Передний и задний край.
        - **5, 6**: Верхний и нижний край.
        - **7**: Центр шкворня.
        """)
        MIN_POINTS = 7
        if st.session_state.pixels_per_meter and len(st.session_state.points) >= MIN_POINTS:
            brand = st.text_input("Марка", "Schmitz")
            model = st.text_input("Модель", "Cargobull")
            trl_w = st.number_input("Ширина (м)", 0.1, value=2.55, step=0.05)
            num_trl = st.number_input("Кол-во осей", 1, value=3, step=1)

            if st.button("Сохранить прицеп в библиотеку"):
                ppm = st.session_state.pixels_per_meter
                pts = st.session_state.points
                axle_spacing = calculate_pixel_distance(pts[0], pts[1]) / (num_trl - 1) / ppm if num_trl > 1 else 0
                params = {'brand': brand, 'model': model, 'length': calculate_pixel_distance(pts[2], pts[3])/ppm, 'height': calculate_pixel_distance(pts[4], pts[5], 'y')/ppm, 'kingpin_offset': calculate_pixel_distance(pts[2], pts[6])/ppm, 'axle_pos_from_rear': calculate_pixel_distance(pts[1], pts[3])/ppm, 'wheel_diameter': calculate_pixel_distance(pts[4], pts[5], 'y')*0.4/ppm, 'width': trl_w, 'num_axles': num_trl, 'axle_spacing': axle_spacing}
                
                new_trailer = SemiTrailer(**params)
                unique_name = new_trailer.get_unique_name()
                if unique_name in st.session_state.library:
                    st.error("Прицеп с таким именем уже существует!")
                else:
                    st.session_state.library[unique_name] = new_trailer
                    st.success(f"Прицеп '{unique_name}' сохранен!")

    # --- ИНТЕРФЕЙС ДЛЯ СБОРКИ АВТОПОЕЗДА ---
    elif vehicle_type == "Сборка автопоезда":
        st.header("2. Сборка")
        tractors_in_library = {name: obj for name, obj in st.session_state.library.items() if isinstance(obj, Tractor)}
        trailers_in_library = {name: obj for name, obj in st.session_state.library.items() if isinstance(obj, SemiTrailer)}

        if not tractors_in_library or not trailers_in_library:
            st.warning("Сначала создайте и сохраните хотя бы один тягач и один прицеп.")
        else:
            selected_tractor_name = st.selectbox("Выберите тягач", list(tractors_in_library.keys()))
            selected_trailer_name = st.selectbox("Выберите полуприцеп", list(trailers_in_library.keys()))
            
            if st.button("Собрать автопоезд"):
                st.session_state.tractor_obj = tractors_in_library[selected_tractor_name]
                st.session_state.trailer_obj = trailers_in_library[selected_trailer_name]
                st.success("Автопоезд собран!")

# --- Основная область ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("2D Чертеж")
    if vehicle_type != "Сборка автопоезда" and uploaded_file is not None:
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
    elif vehicle_type == "Сборка автопоезда":
        st.info("Выберите компоненты из библиотеки для сборки.")
    else:
        st.info("Пожалуйста, загрузите изображение чертежа.")
    
    st.write("Отмеченные точки:")
    if st.session_state.points:
        st.write(st.session_state.points)

with col2:
    st.subheader("3D Модель")
    
    scene = Scene()
    if vehicle_type == "Сборка автопоезда":
        scene.add_articulated_vehicle(st.session_state.tractor_obj, st.session_state.trailer_obj)
    elif vehicle_type == "Создать тягач":
        scene.add(st.session_state.get('tractor_obj', Tractor()))
    elif vehicle_type == "Создать прицеп":
        scene.add(st.session_state.get('trailer_obj', SemiTrailer()))
    elif vehicle_type == "Создать фургон":
        scene.add(st.session_state.get('van_obj', Van()))

    fig = scene.generate_figure()
    st.plotly_chart(fig, use_container_width=True)

st.sidebar.header("Библиотека")
st.sidebar.write(list(st.session_state.library.keys()))
