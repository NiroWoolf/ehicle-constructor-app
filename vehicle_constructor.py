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
    circ_x, circ_y = radius * np.cos(theta), radius * np.sin(theta)
    
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
    body = go.Surface(x=x_grid, y=y_grid, z=z_grid, colorscale=colorscale, showscale=False, name=name, hoverinfo='name')
    
    # Caps
    cap1_vals, cap2_vals = v[0], v[1]
    if axis == 'y':
        cap1 = go.Surface(x=circ_x + cx, y=np.full(num_points, cap1_vals), z=circ_y + cz, colorscale=colorscale, showscale=False, hoverinfo='none')
        cap2 = go.Surface(x=circ_x + cx, y=np.full(num_points, cap2_vals), z=circ_y + cz, colorscale=colorscale, showscale=False, hoverinfo='none')
    elif axis == 'x':
        cap1 = go.Surface(x=np.full(num_points, cap1_vals), y=circ_x + cy, z=circ_y + cz, colorscale=colorscale, showscale=False, hoverinfo='none')
        cap2 = go.Surface(x=np.full(num_points, cap2_vals), y=circ_x + cy, z=circ_y + cz, colorscale=colorscale, showscale=False, hoverinfo='none')
    else: # 'z'
        cap1 = go.Surface(x=circ_x + cx, y=circ_y + cy, z=np.full(num_points, cap1_vals), colorscale=colorscale, showscale=False, hoverinfo='none')
        cap2 = go.Surface(x=circ_x + cx, y=circ_y + cy, z=np.full(num_points, cap2_vals), colorscale=colorscale, showscale=False, hoverinfo='none')
        
    return [body, cap1, cap2]

# --- Классы Сущностей ---

class Tractor:
    """Класс для представления Тягача."""
    def __init__(self, cab_length=2.2, cab_width=2.5, cab_height=2.8,
                 front_axle_pos=1.2, wheelbase=3.8, saddle_pos_from_rear_axle=0.5,
                 num_rear_axles=2, rear_axle_spacing=1.3,
                 wheel_diameter=1.0, wheel_width=0.4):
        self.cab_length = cab_length
        self.cab_width = cab_width
        self.cab_height = cab_height
        self.front_axle_pos = front_axle_pos
        self.wheelbase = wheelbase
        self.saddle_pos_from_rear_axle = saddle_pos_from_rear_axle
        self.num_rear_axles = num_rear_axles
        self.rear_axle_spacing = rear_axle_spacing
        self.wheel_diameter = wheel_diameter
        self.wheel_width = wheel_width
        
        self.wheel_radius = self.wheel_diameter / 2
        self.frame_level_z = self.wheel_diameter * 1.1
        self.first_rear_axle_pos = self.front_axle_pos + self.wheelbase
        self.saddle_pos = self.first_rear_axle_pos + self.saddle_pos_from_rear_axle

    def get_components(self, x_offset=0, y_offset=0, z_offset=0, overall_width=2.55):
        """Возвращает список всех 3D компонентов тягача со смещением."""
        parts = []
        cab_y_offset = y_offset + (overall_width - self.cab_width) / 2
        
        # Кабина
        parts.append(_create_cuboid((x_offset, cab_y_offset, z_offset + self.frame_level_z), 
                                   (self.cab_length, self.cab_width, self.cab_height), 'royalblue', 'Кабина'))
        # Рама
        chassis_len = self.first_rear_axle_pos + self.wheel_radius * 2
        parts.append(_create_cuboid((x_offset, y_offset + (overall_width - 1.0) / 2, z_offset + self.frame_level_z - 0.2), 
                                   (chassis_len, 1.0, 0.2), 'dimgray', 'Рама тягача'))
        # Седло
        parts.append(_create_cuboid((x_offset + self.saddle_pos - 0.5, y_offset + (overall_width - 1.2) / 2, z_offset + self.frame_level_z), 
                                   (1.0, 1.2, 0.05), 'darkslategrey', 'Седло'))
        # Колеса
        track_width = self.cab_width * 0.9
        y_left_local = (self.cab_width - track_width) / 2
        y_right_local = self.cab_width - y_left_local
        
        # Передние
        parts.extend(_create_cylinder((x_offset + self.front_axle_pos, cab_y_offset + y_left_local, z_offset + self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        parts.extend(_create_cylinder((x_offset + self.front_axle_pos, cab_y_offset + y_right_local, z_offset + self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        
        # Задние
        for i in range(self.num_rear_axles):
            axle_x = self.first_rear_axle_pos - (i * self.rear_axle_spacing)
            centers = [(x_offset + axle_x, cab_y_offset + y, z_offset + self.wheel_radius) for y in [y_left_local - self.wheel_width/2, y_left_local + self.wheel_width/2, y_right_local - self.wheel_width/2, y_right_local + self.wheel_width/2]]
            for center in centers: parts.extend(_create_cylinder(center, self.wheel_radius, self.wheel_width, 'y', name='Колесо'))

        return parts

class SemiTrailer:
    """Класс для представления Полуприцепа."""
    def __init__(self, length=13.6, width=2.55, height=2.7,
                 kingpin_offset=1.2, axle_pos_from_rear=2.5,
                 num_axles=3, axle_spacing=1.3,
                 wheel_diameter=1.0, wheel_width=0.4):
        self.length = length
        self.width = width
        self.height = height
        self.kingpin_offset = kingpin_offset
        self.axle_pos_from_rear = axle_pos_from_rear
        self.num_axles = num_axles
        self.axle_spacing = axle_spacing
        self.wheel_diameter = wheel_diameter
        self.wheel_width = wheel_width
        self.wheel_radius = self.wheel_diameter / 2

    def get_components(self, x_offset=0, y_offset=0, z_offset=0):
        """Возвращает список всех 3D компонентов полуприцепа со смещением."""
        parts = []
        # Кузов
        parts.append(_create_cuboid((x_offset, y_offset, z_offset), (self.length, self.width, self.height), 'lightcoral', 'Кузов'))
        # Рама
        parts.append(_create_cuboid((x_offset, y_offset + (self.width - 1.0)/2, z_offset - 0.2), (self.length, 1.0, 0.2), 'dimgray', 'Рама прицепа'))
        # Колеса
        track_width = self.width * 0.9
        y_left_local = (self.width - track_width) / 2
        y_right_local = self.width - y_left_local
        
        first_axle_pos = x_offset + self.length - self.axle_pos_from_rear
        for i in range(self.num_axles):
            axle_x = first_axle_pos - (i * self.axle_spacing)
            centers = [(axle_x, y_offset + y, z_offset - 0.2 - self.wheel_radius) for y in [y_left_local - self.wheel_width/2, y_left_local + self.wheel_width/2, y_right_local - self.wheel_width/2, y_right_local + self.wheel_width/2]]
            for center in centers: parts.extend(_create_cylinder(center, self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
            
        return parts

class Van:
    """Класс для представления Фургона."""
    def __init__(self, body_length=6.0, body_width=2.4, body_height=2.2,
                 cab_length=2.0, front_axle_pos=1.2, wheelbase=4.0,
                 num_rear_axles=1, rear_axle_spacing=0,
                 wheel_diameter=0.8, wheel_width=0.3):
        self.body_length = body_length
        self.body_width = body_width
        self.body_height = body_height
        self.cab_length = cab_length
        self.front_axle_pos = front_axle_pos
        self.wheelbase = wheelbase
        self.num_rear_axles = num_rear_axles
        self.rear_axle_spacing = rear_axle_spacing
        self.wheel_diameter = wheel_diameter
        self.wheel_width = wheel_width
        
        self.wheel_radius = self.wheel_diameter / 2
        self.frame_level_z = self.wheel_diameter * 1.1

    def get_components(self, x_offset=0, y_offset=0, z_offset=0):
        """Возвращает список всех 3D компонентов фургона."""
        parts = []
        # Кабина
        parts.append(_create_cuboid((x_offset, y_offset, z_offset + self.frame_level_z),
                                   (self.cab_length, self.body_width, self.body_height), 'skyblue', 'Кабина фургона'))
        # Кузов
        parts.append(_create_cuboid((x_offset + self.cab_length, y_offset, z_offset + self.frame_level_z),
                                   (self.body_length, self.body_width, self.body_height), 'lightgrey', 'Кузов фургона'))
        # Рама
        chassis_len = self.cab_length + self.body_length
        parts.append(_create_cuboid((x_offset, y_offset + (self.body_width - 1.0)/2, z_offset + self.frame_level_z - 0.2),
                                   (chassis_len, 1.0, 0.2), 'dimgray', 'Рама фургона'))
        # Колеса
        track_width = self.body_width * 0.9
        y_left_local = (self.body_width - track_width) / 2
        y_right_local = self.body_width - y_left_local
        
        # Передние
        parts.extend(_create_cylinder((x_offset + self.front_axle_pos, y_offset + y_left_local, z_offset + self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        parts.extend(_create_cylinder((x_offset + self.front_axle_pos, y_offset + y_right_local, z_offset + self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        
        # Задние
        first_rear_axle_pos = self.front_axle_pos + self.wheelbase
        for i in range(self.num_rear_axles):
            axle_x = first_rear_axle_pos - (i * self.rear_axle_spacing)
            centers = [(x_offset + axle_x, y_offset + y, z_offset + self.wheel_radius) for y in [y_left_local - self.wheel_width/2, y_left_local + self.wheel_width/2, y_right_local - self.wheel_width/2, y_right_local + self.wheel_width/2]]
            for center in centers: parts.extend(_create_cylinder(center, self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
            
        return parts

# --- Класс Сборщика ---

class Scene:
    """Класс для сборки и отображения различных транспортных сущностей."""
    def __init__(self):
        self.components = []

    def add_tractor(self, tractor: Tractor, x=0, y=0, z=0):
        self.components.extend(tractor.get_components(x, y, z, tractor.cab_width))

    def add_trailer(self, trailer: SemiTrailer, x=0, y=0, z=0):
        self.components.extend(trailer.get_components(x, y, z))
        
    def add_van(self, van: Van, x=0, y=0, z=0):
        self.components.extend(van.get_components(x, y, z))

    def add_articulated_vehicle(self, tractor: Tractor, trailer: SemiTrailer):
        trailer_start_x = tractor.saddle_pos - trailer.kingpin_offset
        self.components.extend(tractor.get_components(overall_width=trailer.width))
        self.components.extend(trailer.get_components(trailer_start_x, 0, tractor.frame_level_z))

    def generate_figure(self):
        """Собирает все добавленные компоненты в единую 3D модель."""
        if not self.components:
            return go.Figure()

        fig = go.Figure(data=self.components)
        
        fig.update_layout(
            title='Параметрическая 3D модель',
            scene=dict(
                xaxis=dict(title='Длина (X)'),
                yaxis=dict(title='Ширина (Y)'),
                zaxis=dict(title='Высота (Z)'),
                aspectmode='data',
                aspectratio=dict(x=1, y=1, z=1)
            ),
            margin=dict(l=10, r=10, b=10, t=40)
        )
        return fig
