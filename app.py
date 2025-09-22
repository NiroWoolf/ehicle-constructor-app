import streamlit as st
from vehicle_constructor import Tractor, SemiTrailer, Van, Scene

# --- Инициализация состояния сессии ---
def init_session_state():
    """Инициализирует состояние сессии, если оно еще не создано."""
    defaults = {
        "vehicle_type": "Сборка автопоезда",
        "library": {},
        "current_tractor": Tractor(),
        "current_trailer": SemiTrailer(),
        "current_van": Van()
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- Основное приложение ---
st.set_page_config(layout="wide")
st.title("Движок-Конструктор 3D-моделей")

# --- Боковая панель ---
st.sidebar.header("Управление")

# Главное меню выбора режима
st.session_state.vehicle_type = st.sidebar.selectbox(
    "Выберите режим",
    ("Сборка автопоезда", "Тягач", "Прицеп", "Фургон"),
    key="main_mode_selector"
)

# --- Динамический интерфейс в боковой панели ---

# --- ИНТЕРФЕЙС ДЛЯ ТЯГАЧА ---
if st.session_state.vehicle_type == "Тягач":
    st.sidebar.header("Параметры тягача")
    
    brand = st.sidebar.text_input("Марка", value=st.session_state.current_tractor.brand)
    model = st.sidebar.text_input("Модель", value=st.session_state.current_tractor.model)
    
    st.sidebar.subheader("Габариты")
    cab_length = st.sidebar.number_input("Длина кабины (м)", value=2.2, step=0.1, key="t_cab_l")
    cab_width = st.sidebar.number_input("Ширина кабины (м)", value=2.5, step=0.1, key="t_cab_w")
    cab_height = st.sidebar.number_input("Высота кабины (м)", value=2.8, step=0.1, key="t_cab_h")
    
    st.sidebar.subheader("Шасси")
    front_axle_pos = st.sidebar.number_input("Положение передней оси от бампера (м)", value=1.45, step=0.05, key="t_ax_pos")
    wheelbase = st.sidebar.number_input("Колесная база (м)", value=3.6, step=0.1, key="t_wb")
    saddle_pos_from_rear_axle = st.sidebar.number_input("Смещение седла от центра задней тележки (м)", value=0.5, step=0.05, key="t_saddle")
    
    st.sidebar.subheader("Колеса")
    num_rear_axles = st.sidebar.number_input("Кол-во задних осей", min_value=1, value=2, step=1, key="t_num_ax")
    rear_axle_spacing = st.sidebar.number_input("Расстояние между задними осями (м)", value=1.3, step=0.1, key="t_ax_sp")
    wheel_type = st.sidebar.selectbox("Тип задних колес", ('dual', 'single'), key="t_w_type")
    wheel_diameter = st.sidebar.number_input("Диаметр колес (м)", value=1.0, step=0.05, key="t_w_d")
    wheel_width = st.sidebar.number_input("Ширина колес (м)", value=0.4, step=0.05, key="t_w_w")
    
    if st.sidebar.button("Создать / Обновить"):
        params = {
            'brand': brand, 'model': model, 'cab_length': cab_length, 'cab_width': cab_width,
            'cab_height': cab_height, 'front_axle_pos': front_axle_pos, 'wheelbase': wheelbase,
            'saddle_pos_from_rear_axle': saddle_pos_from_rear_axle, 'num_rear_axles': num_rear_axles,
            'rear_axle_spacing': rear_axle_spacing, 'wheel_type': wheel_type,
            'wheel_diameter': wheel_diameter, 'wheel_width': wheel_width
        }
        st.session_state.current_tractor = Tractor(**params)
        st.sidebar.success("Тягач обновлен!")

    if st.sidebar.button("Сохранить в библиотеку"):
        # Сначала обновляем объект, чтобы сохранить последние введенные данные
        params = {
            'brand': brand, 'model': model, 'cab_length': cab_length, 'cab_width': cab_width,
            'cab_height': cab_height, 'front_axle_pos': front_axle_pos, 'wheelbase': wheelbase,
            'saddle_pos_from_rear_axle': saddle_pos_from_rear_axle, 'num_rear_axles': num_rear_axles,
            'rear_axle_spacing': rear_axle_spacing, 'wheel_type': wheel_type,
            'wheel_diameter': wheel_diameter, 'wheel_width': wheel_width
        }
        st.session_state.current_tractor = Tractor(**params)
        unique_name = st.session_state.current_tractor.get_unique_name()
        if unique_name in st.session_state.library:
            st.sidebar.error("Техника с такой маркой и моделью уже существует!")
        else:
            st.session_state.library[unique_name] = st.session_state.current_tractor
            st.sidebar.success(f"Тягач '{unique_name}' сохранен!")


# --- ИНТЕРФЕЙС ДЛЯ ПРИЦЕПА ---
elif st.session_state.vehicle_type == "Прицеп":
    st.sidebar.header("Параметры прицепа")
    
    brand = st.sidebar.text_input("Марка", value=st.session_state.current_trailer.brand, key="trl_brand")
    model = st.sidebar.text_input("Модель", value=st.session_state.current_trailer.model, key="trl_model")

    st.sidebar.subheader("Габариты кузова")
    length = st.sidebar.number_input("Длина (м)", value=13.6, step=0.1, key="trl_l")
    width = st.sidebar.number_input("Ширина (м)", value=2.55, step=0.1, key="trl_w")
    height = st.sidebar.number_input("Высота (м)", value=2.7, step=0.1, key="trl_h")

    st.sidebar.subheader("Шасси")
    kingpin_offset = st.sidebar.number_input("Смещение шкворня от переднего края (м)", value=1.2, step=0.1, key="trl_k_off")
    axle_pos_from_rear = st.sidebar.number_input("Положение задней оси от заднего края (м)", value=2.5, step=0.1, key="trl_ax_pos")
    num_axles = st.sidebar.number_input("Количество осей", min_value=1, value=3, step=1, key="trl_num_ax")
    axle_spacing = st.sidebar.number_input("Расстояние между осями (м)", value=1.3, step=0.1, key="trl_ax_sp")

    st.sidebar.subheader("Колеса")
    wheel_type = st.sidebar.selectbox("Тип колес", ('single', 'dual'), key="trl_w_type")
    wheel_diameter = st.sidebar.number_input("Диаметр колес (м)", value=1.0, step=0.05, key="trl_w_d")
    wheel_width = st.sidebar.number_input("Ширина колес (м)", value=0.4, step=0.05, key="trl_w_w")

    if st.sidebar.button("Создать / Обновить"):
        params = {
            'brand': brand, 'model': model, 'length': length, 'width': width, 'height': height,
            'kingpin_offset': kingpin_offset, 'axle_pos_from_rear': axle_pos_from_rear,
            'num_axles': num_axles, 'axle_spacing': axle_spacing, 'wheel_type': wheel_type,
            'wheel_diameter': wheel_diameter, 'wheel_width': wheel_width
        }
        st.session_state.current_trailer = SemiTrailer(**params)
        st.sidebar.success("Прицеп обновлен!")
    
    if st.sidebar.button("Сохранить в библиотеку"):
        params = {
            'brand': brand, 'model': model, 'length': length, 'width': width, 'height': height,
            'kingpin_offset': kingpin_offset, 'axle_pos_from_rear': axle_pos_from_rear,
            'num_axles': num_axles, 'axle_spacing': axle_spacing, 'wheel_type': wheel_type,
            'wheel_diameter': wheel_diameter, 'wheel_width': wheel_width
        }
        st.session_state.current_trailer = SemiTrailer(**params)
        unique_name = st.session_state.current_trailer.get_unique_name()
        if unique_name in st.session_state.library:
            st.sidebar.error("Техника с такой маркой и моделью уже существует!")
        else:
            st.session_state.library[unique_name] = st.session_state.current_trailer
            st.sidebar.success(f"Прицеп '{unique_name}' сохранен!")

# --- ИНТЕРФЕЙС ДЛЯ ФУРГОНА ---
elif st.session_state.vehicle_type == "Фургон":
    st.sidebar.header("Параметры фургона")
    
    brand = st.sidebar.text_input("Марка", value=st.session_state.current_van.brand, key="van_brand")
    model = st.sidebar.text_input("Модель", value=st.session_state.current_van.model, key="van_model")

    st.sidebar.subheader("Габариты")
    cab_length = st.sidebar.number_input("Длина кабины (м)", value=2.0, step=0.1, key="van_cab_l")
    body_length = st.sidebar.number_input("Длина кузова (м)", value=4.2, step=0.1, key="van_body_l")
    body_width = st.sidebar.number_input("Ширина кузова (м)", value=2.2, step=0.1, key="van_body_w")
    body_height = st.sidebar.number_input("Высота кузова (м)", value=2.2, step=0.1, key="van_body_h")
    
    st.sidebar.subheader("Шасси")
    front_axle_pos = st.sidebar.number_input("Положение передней оси от бампера (м)", value=1.0, step=0.05, key="van_ax_pos")
    wheelbase = st.sidebar.number_input("Колесная база (м)", value=4.0, step=0.1, key="van_wb")
    
    st.sidebar.subheader("Колеса")
    num_rear_axles = st.sidebar.number_input("Кол-во задних осей", min_value=1, value=1, step=1, key="van_num_ax")
    rear_axle_spacing = st.sidebar.number_input("Расстояние между задними осями (м)", value=1.0, step=0.1, key="van_ax_sp")
    wheel_type = st.sidebar.selectbox("Тип задних колес", ('dual', 'single'), key="van_w_type")
    wheel_diameter = st.sidebar.number_input("Диаметр колес (м)", value=0.8, step=0.05, key="van_w_d")
    wheel_width = st.sidebar.number_input("Ширина колес (м)", value=0.3, step=0.05, key="van_w_w")

    if st.sidebar.button("Создать / Обновить"):
        params = {
            'brand': brand, 'model': model, 'cab_length': cab_length, 'body_length': body_length,
            'body_width': body_width, 'body_height': body_height, 'front_axle_pos': front_axle_pos,
            'wheelbase': wheelbase, 'num_rear_axles': num_rear_axles, 'rear_axle_spacing': rear_axle_spacing,
            'wheel_type': wheel_type, 'wheel_diameter': wheel_diameter, 'wheel_width': wheel_width
        }
        st.session_state.current_van = Van(**params)
        st.sidebar.success("Фургон обновлен!")
    
    if st.sidebar.button("Сохранить в библиотеку"):
        params = {
            'brand': brand, 'model': model, 'cab_length': cab_length, 'body_length': body_length,
            'body_width': body_width, 'body_height': body_height, 'front_axle_pos': front_axle_pos,
            'wheelbase': wheelbase, 'num_rear_axles': num_rear_axles, 'rear_axle_spacing': rear_axle_spacing,
            'wheel_type': wheel_type, 'wheel_diameter': wheel_diameter, 'wheel_width': wheel_width
        }
        st.session_state.current_van = Van(**params)
        unique_name = st.session_state.current_van.get_unique_name()
        if unique_name in st.session_state.library:
            st.sidebar.error("Техника с такой маркой и моделью уже существует!")
        else:
            st.session_state.library[unique_name] = st.session_state.current_van
            st.sidebar.success(f"Фургон '{unique_name}' сохранен!")


# --- ИНТЕРФЕЙС ДЛЯ СБОРКИ ---
elif st.session_state.vehicle_type == "Сборка автопоезда":
    st.sidebar.header("Сборка")
    tractors = {name: obj for name, obj in st.session_state.library.items() if isinstance(obj, Tractor)}
    trailers = {name: obj for name, obj in st.session_state.library.items() if isinstance(obj, SemiTrailer)}
    
    if not tractors or not trailers:
        st.sidebar.warning("Сначала создайте и сохраните в библиотеку хотя бы один тягач и один прицеп.")
    else:
        sel_tractor_name = st.sidebar.selectbox("Выберите тягач", list(tractors.keys()))
        sel_trailer_name = st.sidebar.selectbox("Выберите прицеп", list(trailers.keys()))
        if st.sidebar.button("Собрать автопоезд"):
            st.session_state.current_tractor = st.session_state.library[sel_tractor_name]
            st.session_state.current_trailer = st.session_state.library[sel_trailer_name]
            st.sidebar.success("Автопоезд готов к отображению!")

# --- Основная область и 3D Сцена ---
st.header("3D Модель")
scene = Scene()

if st.session_state.vehicle_type == "Тягач":
    scene.add(st.session_state.current_tractor)
elif st.session_state.vehicle_type == "Прицеп":
    scene.add(st.session_state.current_trailer)
elif st.session_state.vehicle_type == "Фургон":
    scene.add(st.session_state.current_van)
elif st.session_state.vehicle_type == "Сборка автопоезда":
    scene.add_articulated_vehicle(st.session_state.current_tractor, st.session_state.current_trailer)

fig = scene.generate_figure()
st.plotly_chart(fig, use_container_width=True)

st.sidebar.header("Библиотека")
if st.session_state.library:
    st.sidebar.json(list(st.session_state.library.keys()))
else:
    st.sidebar.write("Пусто")


