                 # Параметры прицепа
import plotly.graph_objects as go
import numpy as np

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
        """
        Инициализирует "скелет" транспортного средства с заданными параметрами.

        Args:
            cab_length (float): Длина кабины.
            cab_width (float): Ширина кабины.
            cab_height (float): Высота кабины от рамы.
            wheelbase (float): Колесная база тягача.
            saddle_position_from_rear_axle (float): Смещение седла от задней оси тягача.
            wheel_diameter (float): Диаметр колес.
            wheel_width (float): Ширина колес.
            trailer_length (float): Внутренняя длина полуприцепа.
            trailer_width (float): Внутренняя ширина полуприцепа.
            trailer_height (float): Внутренняя высота полуприцепа.
            kingpin_offset (float): Смещение шкворня от переднего края прицепа.
            trailer_axle_position_from_rear (float): Положение осей прицепа от его заднего края.
        """
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
        """
        Вспомогательный метод для создания одного параллелепипеда (кубоида).

        Args:
            origin (tuple): Координаты (x, y, z) начальной точки.
            dimensions (tuple): Размеры (dx, dy, dz).
            color (str): Цвет фигуры.
            name (str): Имя объекта для легенды.

        Returns:
            go.Mesh3d: Объект сетки для Plotly.
        """
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

    def _create_cylinder(self, center, radius, length, axis='y', color='darkgrey', name='cylinder', num_points=30):
        """
        Вспомогательный метод для создания одного цилиндра.
        """
        cx, cy, cz = center
        theta = np.linspace(0, 2 * np.pi, num_points)
        circ_x = radius * np.cos(theta)
        circ_y = radius * np.sin(theta)

        if axis == 'y':
            v = np.linspace(cy - length / 2, cy + length / 2, 2)
            theta_grid, v_grid = np.meshgrid(theta, v)
            x_grid, y_grid, z_grid = radius * np.cos(theta_grid) + cx, v_grid, radius * np.sin(theta_grid) + cz
        elif axis == 'x':
            v = np.linspace(cx - length / 2, cx + length / 2, 2)
            theta_grid, v_grid = np.meshgrid(theta, v)
            x_grid, y_grid, z_grid = v_grid, radius * np.cos(theta_grid) + cy, radius * np.sin(theta_grid) + cz
        else: # axis == 'z'
            v = np.linspace(cz - length / 2, cz + length / 2, 2)
            theta_grid, v_grid = np.meshgrid(theta, v)
            x_grid, y_grid, z_grid = radius * np.cos(theta_grid) + cx, radius * np.sin(theta_grid) + cy, v_grid

        colorscale = [[0, color], [1, color]]
        body = go.Surface(x=x_grid, y=y_grid, z=z_grid, colorscale=colorscale, showscale=False, name=name, hoverinfo='name')
        
        cap1_vals, cap2_vals = v[0], v[1]
        if axis == 'y':
            cap1 = go.Surface(x=circ_x + cx, y=np.full(num_points, cap1_vals), z=circ_y + cz, colorscale=colorscale, showscale=False, hoverinfo='none')
            cap2 = go.Surface(x=circ_x + cx, y=np.full(num_points, cap2_vals), z=circ_y + cz, colorscale=colorscale, showscale=False, hoverinfo='none')
        elif axis == 'x':
            cap1 = go.Surface(x=np.full(num_points, cap1_vals), y=circ_x + cy, z=circ_y + cz, colorscale=colorscale, showscale=False, hoverinfo='none')
            cap2 = go.Surface(x=np.full(num_points, cap2_vals), y=circ_x + cy, z=circ_y + cz, colorscale=colorscale, showscale=False, hoverinfo='none')
        else: # axis == 'z'
            cap1 = go.Surface(x=circ_x + cx, y=circ_y + cy, z=np.full(num_points, cap1_vals), colorscale=colorscale, showscale=False, hoverinfo='none')
            cap2 = go.Surface(x=circ_x + cx, y=circ_y + cy, z=np.full(num_points, cap2_vals), colorscale=colorscale, showscale=False, hoverinfo='none')

        return [body, cap1, cap2]

    def _create_cab(self):
        """Создает геометрию кабины."""
        origin = (0, (self.trailer_width - self.cab_width) / 2, self.frame_level_z)
        dimensions = (self.cab_length, self.cab_width, self.cab_height)
        return self._create_cuboid(origin, dimensions, color='royalblue', name='Кабина')

    def _create_chassis(self):
        """Создает геометрию рамы тягача."""
        chassis_width = 1.0
        chassis_height = 0.2
        chassis_length = self.rear_axle_pos_x + self.wheel_radius * 2
        origin = (0, (self.trailer_width - chassis_width) / 2, self.frame_level_z - chassis_height)
        dimensions = (chassis_length, chassis_width, chassis_height)
        return self._create_cuboid(origin, dimensions, color='dimgray', name='Рама тягача')

    def _create_saddle(self):
        """Создает седельно-сцепное устройство (пятое колесо)."""
        saddle_width = 1.2
        saddle_length = 1.0
        saddle_height = 0.05
        origin = (
            self.saddle_pos_x - saddle_length / 2,
            (self.trailer_width - saddle_width) / 2,
            self.frame_level_z
        )
        dimensions = (saddle_length, saddle_width, saddle_height)
        return self._create_cuboid(origin, dimensions, color='darkslategrey', name='Седло')

    def _create_wheels(self):
        """Создает геометрию всех колес."""
        wheels = []
        track_width = self.cab_width * 0.9
        y_left = (self.trailer_width - track_width) / 2 - self.wheel_width / 2
        y_right = self.trailer_width - y_left - self.wheel_width
        
        # Передние колеса
        center_fl = (self.front_axle_pos_x, y_left + self.wheel_width/2, self.wheel_radius)
        center_fr = (self.front_axle_pos_x, y_right + self.wheel_width/2, self.wheel_radius)
        wheels.extend(self._create_cylinder(center_fl, self.wheel_radius, self.wheel_width, axis='y', name='Колесо'))
        wheels.extend(self._create_cylinder(center_fr, self.wheel_radius, self.wheel_width, axis='y', name='Колесо'))

        # Задние колеса тягача (сдвоенные)
        centers_rear_tractor = [
            (self.rear_axle_pos_x, y_left + self.wheel_width*1.5, self.wheel_radius),
            (self.rear_axle_pos_x, y_left - self.wheel_width*0.5, self.wheel_radius),
            (self.rear_axle_pos_x, y_right - self.wheel_width*0.5, self.wheel_radius),
            (self.rear_axle_pos_x, y_right + self.wheel_width*1.5, self.wheel_radius)
        ]
        for center in centers_rear_tractor:
            wheels.extend(self._create_cylinder(center, self.wheel_radius, self.wheel_width, axis='y', name='Колесо'))

        # Колеса прицепа (сдвоенные)
        trailer_axle_x = self.trailer_start_x + self.trailer_length - self.trailer_axle_position_from_rear
        centers_trailer = [
            (trailer_axle_x, y_left + self.wheel_width*1.5, self.wheel_radius),
            (trailer_axle_x, y_left - self.wheel_width*0.5, self.wheel_radius),
            (trailer_axle_x, y_right - self.wheel_width*0.5, self.wheel_radius),
            (trailer_axle_x, y_right + self.wheel_width*1.5, self.wheel_radius)
        ]
        for center in centers_trailer:
            wheels.extend(self._create_cylinder(center, self.wheel_radius, self.wheel_width, axis='y', name='Колесо'))
        
        return wheels

    def _create_trailer_body(self):
        """Создает геометрию кузова полуприцепа."""
        trailer_frame_height = 0.2
        origin = (self.trailer_start_x, 0, self.frame_level_z - trailer_frame_height + trailer_frame_height) # Сидит на раме прицепа
        dimensions = (self.trailer_length, self.trailer_width, self.trailer_height)
        return self._create_cuboid(origin, dimensions, color='lightcoral', name='Кузов полуприцепа')

    def _create_trailer_frame(self):
        """Создает геометрию рамы полуприцепа."""
        frame_width = 1.0
        frame_height = 0.2
        origin = (
            self.trailer_start_x,
            (self.trailer_width - frame_width) / 2,
            self.frame_level_z - frame_height
        )
        dimensions = (self.trailer_length, frame_width, frame_height)
        return self._create_cuboid(origin, dimensions, color='dimgray', name='Рама полуприцепа')

    def generate_figure(self):
        """
        Собирает все части вместе и возвращает готовый объект go.Figure для отображения.
        """
        parts = [
            self._create_cab(),
            self._create_chassis(),
            self._create_saddle(),
            self._create_trailer_body(),
            self._create_trailer_frame(),
        ]
        parts.extend(self._create_wheels())

        fig = go.Figure(data=parts)

        max_dim = max(self.trailer_start_x + self.trailer_length, self.trailer_width, self.frame_level_z + self.cab_height)
        
        fig.update_layout(
            title='Параметрическая 3D модель тягача с полуприцепом',
            scene=dict(
                xaxis=dict(title='Длина (X)', range=[0, max_dim*1.1]),
                yaxis=dict(title='Ширина (Y)', range=[-max_dim*0.1, max_dim*1.1]),
                zaxis=dict(title='Высота (Z)', range=[0, max_dim*1.1]),
                aspectmode='data'
            ),
            margin=dict(l=10, r=10, b=10, t=40)
        )
        return fig

# --- Пример использования ---
if __name__ == '__main__':
    my_truck = ParametricVehicle(
        cab_length=2.3, cab_width=2.5, cab_height=2.8,
        wheelbase=3.7, saddle_position_from_rear_axle=0.6,
        wheel_diameter=1.05, wheel_width=0.4,
        trailer_length=13.6, trailer_width=2.55, trailer_height=2.7,
        kingpin_offset=1.2, trailer_axle_position_from_rear=2.5 # Увеличил, чтобы колеса были дальше от края
    )
    fig = my_truck.generate_figure()
    fig.show()
