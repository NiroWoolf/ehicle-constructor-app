import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
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
        image = Image.open(uploaded_file).convert("RGB")
        
        MAX_WIDTH = 700
        width, height = image.size
        if width > MAX_WIDTH:
            new_height = int(MAX_WIDTH * height / width)
            image = image.resize((MAX_WIDTH, new_height))

        # --- ОТЛАДОЧНАЯ СТРОКА ---
        # Показываем изображение стандартным способом, чтобы проверить, что оно корректно обрабатывается
        st.caption("Отладочная информация: изображение, которое мы передаем в холст.")
        st.image(image)
        # --- КОНЕЦ ОТЛАДОЧНОГО БЛОКА ---

        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=3,
            stroke_color="red",
            background_image=image,
            update_streamlit=True,
            height=image.height,
            width=image.width,
            drawing_mode="point",
            key="canvas",
        )

        if canvas_result.json_data is not None and canvas_result.json_data["objects"]:
            new_point_data = canvas_result.json_data["objects"][-1]
            is_new = True
            for p in st.session_state["points"]:
                if p['left'] == new_point_data['left'] and p['top'] == new_point_data['top']:
                    is_new = False
                    break
            
            if is_new:
                st.session_state["points"].append(new_point_data)

    else:
        st.info("Пожалуйста, загрузите изображение чертежа в боковой панели.")
    
    st.write("Отмеченные точки (в пикселях):")
    st.dataframe(st.session_state["points"])


with col2:
    st.subheader("3D Модель")
    
    default_truck = ParametricVehicle()
    fig = default_truck.generate_figure()
    st.plotly_chart(fig, use_container_width=True)
