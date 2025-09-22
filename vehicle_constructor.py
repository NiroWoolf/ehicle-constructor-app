import plotly.graph_objects as go
import numpy as np

# --- Вспомогательные функции отрисовки ---

def _create_cuboid(origin, dimensions, color='lightblue', name='cuboid'):
    """Создает параллелепипед (кубоид) для Plotly."""
    x0, y0, z0 = origin
    dx, dy, dz = dimensions
    vertices = np.array([
        [x0, y0, z0], [x0 + dx, y0, z0], [x0 + dx, y0 + dy, z0], [x0, y0 + dy, z0],
        [x0, y0, z0 + dz], [x0 + dx, y0, z0 + dz], [x0 + dx, y0 + dy, z0 + dz], [x0, y0 + dy, z0 + dz]
    ])
    faces = np.array([
        [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7], [0, 4, 5], [0, 5, 1],
        [1, 5, 6], [1, 6, 2], [2, 6, 7], [2, 7, 3], [3, 7, 4], [3, 4, 0]
    ])
    return go.Mesh3d(
        x=vertices[:, 0], y=vertices[:, 1], z=vertices[:, 2],
        i=faces[:, 0], j=faces[:, 1], k=faces[:, 2],
        color=color, opacity=1.0, name=name, hoverinfo='name'
    )

def _create_cylinder(center, radius, length, axis='y', color='darkgrey', name='cylinder', num_points=30):
    """Создает цилиндр для Plotly."""
    cx, cy, cz = center
    theta = np.linspace(0, 2 * np.pi, num_points)
    
    if axis == 'y':
        v = np.linspace(cy - length / 2, cy + length / 2, 2)
        theta_grid, v_grid = np.meshgrid(theta, v)
        x_grid, y_grid, z_grid = radius * np.cos(theta_grid) + cx, v_grid, radius * np.sin(theta_grid) + cz
    elif axis == 'x':
        v = np.linspace(cx - length / 2, cx + length / 2, 2)
        theta_grid, v_grid = np.meshgrid(theta, v)
        x_grid, y_grid, z_grid = v_grid, radius * np.cos(theta_grid) + cy, radius * np.sin(theta_grid) + cz
    else: # 'z'
        v = np.linspace(cz - length / 2, cz + length / 2, 2)
        theta_grid, v_grid = np.meshgrid(theta, v)
        x_grid, y_grid, z_grid = radius * np.cos(theta_grid) + cx, radius * np.sin(theta_grid) + cy, v_grid
        
    colorscale = [[0, color], [1, color]]
    return go.Surface(x=x_grid, y=y_grid, z=z_grid, colorscale=colorscale, showscale=False, name=name, hoverinfo='name')

# --- Классы Сущностей ---

class Tractor:
    """Класс для представления Тягача."""
    def __init__(self, brand="Tractor", model="Default", cab_length=2.2, cab_width=2.5, cab_height=2.8,
                 front_axle_pos=1.45, wheelbase=3.6, saddle_pos_from_rear_axle=0.5,
                 num_rear_axles=2, rear_axle_spacing=1.3, wheel_type='dual',
                 wheel_diameter=1.0, wheel_width=0.4):
        self.brand = brand
        self.model = model
        self.cab_length = cab_length
        self.cab_width = cab_width
        self.cab_height = cab_height
        self.front_axle_pos = front_axle_pos
        self.wheelbase = wheelbase
        self.saddle_pos_from_rear_axle = saddle_pos_from_rear_axle
        self.num_rear_axles = num_rear_axles
        self.rear_axle_spacing = rear_axle_spacing
        self.wheel_type = wheel_type
        self.wheel_diameter = wheel_diameter
        self.wheel_width = wheel_width
        
        self.wheel_radius = self.wheel_diameter / 2
        self.frame_level_z = self.wheel_radius + 0.3 # Более реалистичная высота рамы
        self.first_rear_axle_pos = self.front_axle_pos + self.wheelbase
        self.saddle_pos = self.first_rear_axle_pos + self.saddle_pos_from_rear_axle

    def get_unique_name(self):
        return f"{self.brand} {self.model} (Тягач)"

    def get_components(self, x_offset=0, y_offset=0, z_offset=0):
        """Возвращает список всех 3D компонентов тягача со смещением."""
        parts = []
        
        # TODO: Заменить на загрузку .gltf модели кабины
        parts.append(_create_cuboid((x_offset, y_offset, z_offset + self.frame_level_z), 
                                   (self.cab_length, self.cab_width, self.cab_height), 'royalblue', 'Кабина'))
        
        chassis_len = self.first_rear_axle_pos + (self.num_rear_axles -1) * self.rear_axle_spacing + self.saddle_pos_from_rear_axle + 0.5
        frame_width = 1.0
        parts.append(_create_cuboid((x_offset, y_offset + (self.cab_width - frame_width) / 2, z_offset + self.frame_level_z - 0.2), 
                                   (chassis_len, frame_width, 0.2), 'dimgray', 'Рама тягача'))
        saddle_x_center = self.first_rear_axle_pos + self.saddle_pos_from_rear_axle
        saddle_width = 1.2
        parts.append(_create_cuboid((x_offset + saddle_x_center - 0.5, y_offset + (self.cab_width - saddle_width) / 2, z_offset + self.frame_level_z), 
                                   (1.0, saddle_width, 0.05), 'darkslategrey', 'Седло'))
        
        y_left_center_single = y_offset + self.wheel_width / 2
        y_right_center_single = y_offset + self.cab_width - self.wheel_width / 2
        
        y_left_center_dual = y_offset + self.wheel_width
        y_right_center_dual = y_offset + self.cab_width - self.wheel_width

        parts.append(_create_cylinder((x_offset + self.front_axle_pos, y_left_center_single, z_offset + self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        parts.append(_create_cylinder((x_offset + self.front_axle_pos, y_right_center_single, z_offset + self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        
        for i in range(self.num_rear_axles):
            axle_x = self.first_rear_axle_pos + (i * self.rear_axle_spacing)
            if self.wheel_type == 'dual':
                centers = [
                    (x_offset + axle_x, y_left_center_dual - self.wheel_width/2, z_offset + self.wheel_radius),
                    (x_offset + axle_x, y_left_center_dual + self.wheel_width/2, z_offset + self.wheel_radius),
                    (x_offset + axle_x, y_right_center_dual - self.wheel_width/2, z_offset + self.wheel_radius),
                    (x_offset + axle_x, y_right_center_dual + self.wheel_width/2, z_offset + self.wheel_radius)
                ]
            else: # single
                centers = [
                    (x_offset + axle_x, y_left_center_single, z_offset + self.wheel_radius),
                    (x_offset + axle_x, y_right_center_single, z_offset + self.wheel_radius)
                ]
            for center in centers: 
                parts.append(_create_cylinder(center, self.wheel_radius, self.wheel_width, 'y', name='Колесо'))

        return parts

class SemiTrailer:
    """Класс для представления Полуприцепа."""
    def __init__(self, brand="Trailer", model="Default", length=13.6, width=2.55, height=2.7,
                 kingpin_offset=1.2, axle_pos_from_rear=2.5,
                 num_axles=3, axle_spacing=1.3, wheel_type='single',
                 wheel_diameter=1.0, wheel_width=0.4):
        self.brand = brand
        self.model = model
        self.length = length
        self.width = width
        self.height = height
        self.kingpin_offset = kingpin_offset
        self.axle_pos_from_rear = axle_pos_from_rear
        self.num_axles = num_axles
        self.axle_spacing = axle_spacing
        self.wheel_type = wheel_type
        self.wheel_diameter = wheel_diameter
        self.wheel_width = wheel_width
        self.wheel_radius = self.wheel_diameter / 2

    def get_unique_name(self):
        return f"{self.brand} {self.model} (Прицеп)"

    def get_components(self, x_offset=0, y_offset=0, z_offset=0):
        """Возвращает список всех 3D компонентов полуприцепа со смещением."""
        parts = []

        parts.append(_create_cuboid((x_offset, y_offset, z_offset), (self.length, self.width, self.height), 'lightcoral', 'Кузов'))
        frame_width = 1.0
        parts.append(_create_cuboid((x_offset, y_offset + (self.width - frame_width)/2, z_offset - 0.2), (self.length, frame_width, 0.2), 'dimgray', 'Рама прицепа'))
        
        y_left_center_single = y_offset + self.wheel_width / 2
        y_right_center_single = y_offset + self.width - self.wheel_width / 2
        
        y_left_center_dual = y_offset + self.wheel_width
        y_right_center_dual = y_offset + self.width - self.wheel_width
        
        first_axle_pos = self.length - self.axle_pos_from_rear
        for i in range(self.num_axles):
            axle_x = x_offset + first_axle_pos - (i * self.axle_spacing)
            if self.wheel_type == 'dual':
                centers = [
                    (axle_x, y_left_center_dual - self.wheel_width/2, z_offset - 0.2 + self.wheel_radius),
                    (axle_x, y_left_center_dual + self.wheel_width/2, z_offset - 0.2 + self.wheel_radius),
                    (axle_x, y_right_center_dual - self.wheel_width/2, z_offset - 0.2 + self.wheel_radius),
                    (axle_x, y_right_center_dual + self.wheel_width/2, z_offset - 0.2 + self.wheel_radius)
                ]
            else: # single
                centers = [
                    (axle_x, y_left_center_single, z_offset - 0.2 + self.wheel_radius),
                    (axle_x, y_right_center_single, z_offset - 0.2 + self.wheel_radius)
                ]
            for center in centers: 
                parts.append(_create_cylinder(center, self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
            
        return parts
        
class Van:
    """Класс для представления Фургона."""
    def __init__(self, brand="Van", model="Default", body_length=6.0, body_width=2.4, body_height=2.2,
                 cab_length=2.0, front_axle_pos=1.2, wheelbase=4.0,
                 num_rear_axles=1, rear_axle_spacing=0, wheel_type='dual',
                 wheel_diameter=0.8, wheel_width=0.3):
        self.brand = brand
        self.model = model
        self.body_length = body_length
        self.body_width = body_width
        self.body_height = body_height
        self.cab_length = cab_length
        self.front_axle_pos = front_axle_pos
        self.wheelbase = wheelbase
        self.num_rear_axles = num_rear_axles
        self.rear_axle_spacing = rear_axle_spacing
        self.wheel_type = wheel_type
        self.wheel_diameter = wheel_diameter
        self.wheel_width = wheel_width
        
        self.wheel_radius = self.wheel_diameter / 2
        self.frame_level_z = self.wheel_radius + 0.3
    
    def get_unique_name(self):
        return f"{self.brand} {self.model} (Фургон)"

    def get_components(self, x_offset=0, y_offset=0, z_offset=0):
        """Возвращает список всех 3D компонентов фургона."""
        parts = []
        
        parts.append(_create_cuboid((x_offset, y_offset, z_offset + self.frame_level_z),
                                   (self.cab_length, self.body_width, self.body_height), 'skyblue', 'Кабина фургона'))
        parts.append(_create_cuboid((x_offset + self.cab_length, y_offset, z_offset + self.frame_level_z),
                                   (self.body_length, self.body_width, self.body_height), 'lightgrey', 'Кузов фургона'))
        chassis_len = self.cab_length + self.body_length
        frame_width = 1.0
        parts.append(_create_cuboid((x_offset, y_offset + (self.body_width - frame_width)/2, z_offset + self.frame_level_z - 0.2),
                                   (chassis_len, frame_width, 0.2), 'dimgray', 'Рама фургона'))
        
        y_left_center_single = y_offset + self.wheel_width / 2
        y_right_center_single = y_offset + self.body_width - self.wheel_width / 2

        y_left_center_dual = y_offset + self.wheel_width
        y_right_center_dual = y_offset + self.body_width - self.wheel_width
        
        parts.append(_create_cylinder((x_offset + self.front_axle_pos, y_left_center_single, z_offset + self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        parts.append(_create_cylinder((x_offset + self.front_axle_pos, y_right_center_single, z_offset + self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        
        first_rear_axle_pos = self.front_axle_pos + self.wheelbase
        for i in range(self.num_rear_axles):
            axle_x = first_rear_axle_pos + (i * self.rear_axle_spacing)
            if self.wheel_type == 'dual':
                 centers = [
                    (x_offset + axle_x, y_left_center_dual - self.wheel_width/2, z_offset + self.wheel_radius),
                    (x_offset + axle_x, y_left_center_dual + self.wheel_width/2, z_offset + self.wheel_radius),
                    (x_offset + axle_x, y_right_center_dual - self.wheel_width/2, z_offset + self.wheel_radius),
                    (x_offset + axle_x, y_right_center_dual + self.wheel_width/2, z_offset + self.wheel_radius)
                ]
            else: # single
                centers = [
                    (x_offset + axle_x, y_left_center_single, z_offset + self.wheel_radius),
                    (x_offset + axle_x, y_right_center_single, z_offset + self.wheel_radius)
                ]
            for center in centers: 
                parts.append(_create_cylinder(center, self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
            
        return parts

# --- Класс Сборщика ---
class Scene:
    """Класс для сборки и отображения различных транспортных сущностей."""
    def __init__(self):
        self.components = []

    def add(self, vehicle, x=0, y=0, z=0):
        """Универсальный метод для добавления любого транспортного средства на сцену."""
        if vehicle:
            self.components.extend(vehicle.get_components(x_offset=x, y_offset=y, z_offset=z))

    def add_articulated_vehicle(self, tractor, trailer):
        """Добавляет сцепку тягача и полуприцепа на сцену."""
        if tractor and trailer:
            trailer_start_x = tractor.saddle_pos - trailer.kingpin_offset
            y_offset_tractor = (trailer.width - tractor.cab_width) / 2
            
            self.add(tractor, y=y_offset_tractor)
            self.add(trailer, x=trailer_start_x, z=tractor.frame_level_z)

    def generate_figure(self):
        """Собирает все добавленные компоненты в единую 3D модель."""
        if not self.components:
            fig = go.Figure()
        else:
            fig = go.Figure(data=self.components)
        
        fig.update_layout(
            title_text='3D Модель',
            scene=dict(
                xaxis=dict(title='Длина (X)', autorange="reversed"),
                yaxis=dict(title='Ширина (Y)'),
                zaxis=dict(title='Высота (Z)'),
                aspectmode='data',
            ),
            margin=dict(l=10, r=10, b=10, t=40)
        )
        return fig

