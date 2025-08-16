import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
# Убедитесь, что файл vehicle_constructor.py находится в той же папке
from vehicle_constructor import ParametricVehicle 

# --- Основное приложение Streamlit ---

st.set_page_config(layout="wide")
st.title("Движок-Конструктор 3D-моделей (Этап 2)")

# --- Боковая панель для управления ---
st.sidebar.header("Управление")
uploaded_file = st.sidebar.file_uploader("Загрузите чертеж (PNG, JPG)", type=["png", "jpg", "jpeg"])
st.sidebar.info("Кликните на чертеж, чтобы получить координаты точки.")

# --- Основная область ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("2D Чертеж")
    if uploaded_file is not None:
        # Открываем изображение
        image = Image.open(uploaded_file)
        
        # Создаем интерактивный холст
        # `update_streamlit` = True означает, что приложение будет обновляться при каждом действии
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Цвет заливки (не используется для кликов)
            stroke_width=2,
            stroke_color="#FF0000",
            background_image=image,
            update_streamlit=True,
            height=image.height,
            width=image.width,
            drawing_mode="point", # Режим "точка" для отслеживания кликов
            key="canvas",
        )

        # Отображаем координаты последнего клика
        if canvas_result.json_data is not None:
            # Проверяем, есть ли объекты (точки) на холсте
            if canvas_result.json_data["objects"]:
                # Берем последнюю нарисованную точку
                last_point = canvas_result.json_data["objects"][-1]
                x = last_point["left"]
                y = last_point["top"]
                st.write(f"Последний клик (пиксели): X={x}, Y={y}")
            else:
                st.write("Кликните на изображение, чтобы отметить точку.")

    else:
        st.info("Пожалуйста, загрузите изображение чертежа в боковой панели.")

with col2:
    st.subheader("3D Модель")
    # Создаем экземпляр грузовика с параметрами по умолчанию
    default_truck = ParametricVehicle()
    fig = default_truck.generate_figure()
    
    # Отображаем 3D модель
    st.plotly_chart(fig, use_container_width=True)
