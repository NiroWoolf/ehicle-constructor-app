import streamlit as st
from PIL import Image
import plotly.graph_objects as go
import numpy as np

# Импортируем наш класс из предыдущего файла.
# Для этого он должен лежать в той же папке под именем, например, vehicle_constructor.py
# from vehicle_constructor import ParametricVehicle 

# --- КОПИЯ КЛАССА ДЛЯ АВТОНОМНОЙ РАБОТЫ ---
# Чтобы этот скрипт работал сам по себе, я временно скопировал класс ParametricVehicle сюда.
# В будущем мы будем его импортировать.
class ParametricVehicle:
    """
    Класс для процедурной генерации 3D-модели седельного тягача с полуприцепом.
    Модель создается на основе набора геометрических параметров и отображается с помощью Plotly.
    """
    def __init__(self,
                 # Параметры тягача
                 cab_length=2.2, cab_width=2.5, cab_height=2.8,
                 wheelbase=3.8, saddle_position_from_rear_axle=0.5,
                 # Параметры колес
                 wheel_diameter=1.0, wheel_width=0.4,
                 # Параметры прицепа
                 trailer_length=13.6, trailer_width=2.55, trailer_height=2.7,
                 kingpin_offset=1.2, trailer_axle_position_from_rear=1.3):
        # Сохраняем все параметры
        self.cab_length = cab_length
        self.cab_width = cab_width
        self.cab_height = cab_height
        self.wheelbase = wheelbase
        self.saddle_position_from_rear_axle = saddle_position_from_rear_axle
        self.wheel_diameter = wheel_diameter
        self.wheel_width = wheel_width
        self.trailer_length = trailer_length
        self.trailer_width = trailer_width
        self.trailer_height = trailer_height
        self.kingpin_offset = kingpin_offset
        self.trailer_axle_position_from_rear = trailer_axle_position_from_rear

        # Внутренние расчетные параметры для позиционирования
        self.wheel_radius = self.wheel_diameter / 2
        self.frame_level_z = self.wheel_diameter * 1.1 # Высота уровня рамы чуть выше колес
        self.front_axle_pos_x = self.cab_length * 0.4 # Положение передней оси
        self.rear_axle_pos_x = self.front_axle_pos_x + self.wheelbase
        self.saddle_pos_x = self.rear_axle_pos_x + self.saddle_position_from_rear_axle
        self.trailer_start_x = self.saddle_pos_x - self.kingpin_offset

    def _create_cuboid(self, origin, dimensions, color='lightblue', name='cuboid'):
        x0, y0, z0 = origin
        dx, dy, dz = dimensions
        vertices = np.array([[x0,y0,z0],[x0+dx,y0,z0],[x0+dx,y0+dy,z0],[x0,y0+dy,z0],[x0,y0,z0+dz],[x0+dx,y0,z0+dz],[x0+dx,y0+dy,z0+dz],[x0,y0+dy,z0+dz]])
        faces = np.array([[0,1,2],[0,2,3],[4,5,6],[4,6,7],[0,4,5],[0,5,1],[1,5,6],[1,6,2],[2,6,7],[2,7,3],[3,7,4],[3,4,0]])
        return go.Mesh3d(x=vertices[:,0],y=vertices[:,1],z=vertices[:,2],i=faces[:,0],j=faces[:,1],k=faces[:,2],color=color,opacity=1.0,name=name,hoverinfo='name')

    def _create_cylinder(self, center, radius, length, axis='y', color='darkgrey', name='cylinder', num_points=30):
        cx, cy, cz = center
        theta = np.linspace(0, 2*np.pi, num_points)
        circ_x, circ_y = radius * np.cos(theta), radius * np.sin(theta)
        if axis == 'y':
            v = np.linspace(cy - length/2, cy + length/2, 2)
            theta_grid, v_grid = np.meshgrid(theta, v)
            x_grid, y_grid, z_grid = radius*np.cos(theta_grid)+cx, v_grid, radius*np.sin(theta_grid)+cz
        elif axis == 'x':
            v = np.linspace(cx - length/2, cx + length/2, 2)
            theta_grid, v_grid = np.meshgrid(theta, v)
            x_grid, y_grid, z_grid = v_grid, radius*np.cos(theta_grid)+cy, radius*np.sin(theta_grid)+cz
        else:
            v = np.linspace(cz - length/2, cz + length/2, 2)
            theta_grid, v_grid = np.meshgrid(theta, v)
            x_grid, y_grid, z_grid = radius*np.cos(theta_grid)+cx, radius*np.sin(theta_grid)+cy, v_grid
        colorscale = [[0, color], [1, color]]
        body = go.Surface(x=x_grid, y=y_grid, z=z_grid, colorscale=colorscale, showscale=False, name=name, hoverinfo='name')
        cap1_vals, cap2_vals = v[0], v[1]
        if axis == 'y':
            cap1 = go.Surface(x=circ_x+cx, y=np.full(num_points, cap1_vals), z=circ_y+cz, colorscale=colorscale, showscale=False, hoverinfo='none')
            cap2 = go.Surface(x=circ_x+cx, y=np.full(num_points, cap2_vals), z=circ_y+cz, colorscale=colorscale, showscale=False, hoverinfo='none')
        elif axis == 'x':
            cap1 = go.Surface(x=np.full(num_points, cap1_vals), y=circ_x+cy, z=circ_y+cz, colorscale=colorscale, showscale=False, hoverinfo='none')
            cap2 = go.Surface(x=np.full(num_points, cap2_vals), y=circ_x+cy, z=circ_y+cz, colorscale=colorscale, showscale=False, hoverinfo='none')
        else:
            cap1 = go.Surface(x=circ_x+cx, y=circ_y+cy, z=np.full(num_points, cap1_vals), colorscale=colorscale, showscale=False, hoverinfo='none')
            cap2 = go.Surface(x=circ_x+cx, y=circ_y+cy, z=np.full(num_points, cap2_vals), colorscale=colorscale, showscale=False, hoverinfo='none')
        return [body, cap1, cap2]
    
    def _create_cab(self):
        origin = (0, (self.trailer_width - self.cab_width) / 2, self.frame_level_z)
        return self._create_cuboid(origin, (self.cab_length, self.cab_width, self.cab_height), color='royalblue', name='Кабина')

    def _create_chassis(self):
        chassis_width, chassis_height, chassis_length = 1.0, 0.2, self.rear_axle_pos_x + self.wheel_radius*2
        origin = (0, (self.trailer_width - chassis_width)/2, self.frame_level_z - chassis_height)
        return self._create_cuboid(origin, (chassis_length, chassis_width, chassis_height), color='dimgray', name='Рама тягача')

    def _create_saddle(self):
        saddle_width, saddle_length, saddle_height = 1.2, 1.0, 0.05
        origin = (self.saddle_pos_x - saddle_length/2, (self.trailer_width - saddle_width)/2, self.frame_level_z)
        return self._create_cuboid(origin, (saddle_length, saddle_width, saddle_height), color='darkslategrey', name='Седло')

    def _create_wheels(self):
        wheels = []
        track_width = self.cab_width * 0.9
        y_left = (self.trailer_width - track_width) / 2 - self.wheel_width / 2
        y_right = self.trailer_width - y_left - self.wheel_width
        center_fl = (self.front_axle_pos_x, y_left + self.wheel_width/2, self.wheel_radius)
        center_fr = (self.front_axle_pos_x, y_right + self.wheel_width/2, self.wheel_radius)
        wheels.extend(self._create_cylinder(center_fl, self.wheel_radius, self.wheel_width, axis='y', name='Колесо'))
        wheels.extend(self._create_cylinder(center_fr, self.wheel_radius, self.wheel_width, axis='y', name='Колесо'))
        centers_rear_tractor = [(self.rear_axle_pos_x, y, self.wheel_radius) for y in [y_left+self.wheel_width*1.5, y_left-self.wheel_width*0.5, y_right-self.wheel_width*0.5, y_right+self.wheel_width*1.5]]
        for center in centers_rear_tractor: wheels.extend(self._create_cylinder(center, self.wheel_radius, self.wheel_width, axis='y', name='Колесо'))
        trailer_axle_x = self.trailer_start_x + self.trailer_length - self.trailer_axle_position_from_rear
        centers_trailer = [(trailer_axle_x, y, self.wheel_radius) for y in [y_left+self.wheel_width*1.5, y_left-self.wheel_width*0.5, y_right-self.wheel_width*0.5, y_right+self.wheel_width*1.5]]
        for center in centers_trailer: wheels.extend(self._create_cylinder(center, self.wheel_radius, self.wheel_width, axis='y', name='Колесо'))
        return wheels

    def _create_trailer_body(self):
        trailer_frame_height = 0.2
        origin = (self.trailer_start_x, 0, self.frame_level_z)
        return self._create_cuboid(origin, (self.trailer_length, self.trailer_width, self.trailer_height), color='lightcoral', name='Кузов полуприцепа')

    def _create_trailer_frame(self):
        frame_width, frame_height = 1.0, 0.2
        origin = (self.trailer_start_x, (self.trailer_width - frame_width)/2, self.frame_level_z - frame_height)
        return self._create_cuboid(origin, (self.trailer_length, frame_width, frame_height), color='dimgray', name='Рама полуприцепа')

    def generate_figure(self):
        parts = [self._create_cab(), self._create_chassis(), self._create_saddle(), self._create_trailer_body(), self._create_trailer_frame()]
        parts.extend(self._create_wheels())
        fig = go.Figure(data=parts)
        max_dim = max(self.trailer_start_x + self.trailer_length, self.trailer_width, self.frame_level_z + self.cab_height)
        fig.update_layout(title='Параметрическая 3D модель', scene=dict(xaxis=dict(title='Длина (X)',range=[0,max_dim*1.1]), yaxis=dict(title='Ширина (Y)',range=[-max_dim*0.1,max_dim*1.1]), zaxis=dict(title='Высота (Z)',range=[0,max_dim*1.1]), aspectmode='data'), margin=dict(l=10,r=10,b=10,t=40))
        return fig

# --- Основное приложение Streamlit ---

st.set_page_config(layout="wide")
st.title("Движок-Конструктор 3D-моделей (Этап 2)")

# --- Боковая панель для управления ---
st.sidebar.header("Управление")
uploaded_file = st.sidebar.file_uploader("Загрузите чертеж (PNG, JPG)", type=["png", "jpg", "jpeg"])

# --- Основная область ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("2D Чертеж")
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)
    else:
        st.info("Пожалуйста, загрузите изображение чертежа в боковой панели.")

with col2:
    st.subheader("3D Модель")
    # Создаем экземпляр грузовика с параметрами по умолчанию
    # В будущем эти параметры будут браться из чертежа
    default_truck = ParametricVehicle()
    fig = default_truck.generate_figure()
    
    # Отображаем 3D модель
    st.plotly_chart(fig, use_container_width=True)

