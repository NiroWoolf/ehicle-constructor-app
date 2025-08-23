import plotly.graph_objects as go
import numpy as np

def _create_cuboid(origin, dimensions, color='lightblue', name='cuboid'):
    x0, y0, z0 = origin
    dx, dy, dz = dimensions
    vertices = np.array([[x0,y0,z0],[x0+dx,y0,z0],[x0+dx,y0+dy,z0],[x0,y0+dy,z0],[x0,y0,z0+dz],[x0+dx,y0,z0+dz],[x0+dx,y0+dy,z0+dz],[x0,y0+dy,z0+dz]])
    faces = np.array([[0,1,2],[0,2,3],[4,5,6],[4,6,7],[0,4,5],[0,5,1],[1,5,6],[1,6,2],[2,6,7],[2,7,3],[3,7,4],[3,4,0]])
    return go.Mesh3d(x=vertices[:,0],y=vertices[:,1],z=vertices[:,2],i=faces[:,0],j=faces[:,1],k=faces[:,2],color=color,opacity=1.0,name=name,hoverinfo='name')

def _create_cylinder(center, radius, length, axis='y', color='darkgrey', name='cylinder', num_points=30):
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

class Tractor:
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

    def get_components(self, overall_width):
        """Возвращает список всех 3D компонентов тягача."""
        parts = []
        # Кабина
        parts.append(_create_cuboid((0, (overall_width - self.cab_width) / 2, self.frame_level_z), 
                                   (self.cab_length, self.cab_width, self.cab_height), 'royalblue', 'Кабина'))
        # Рама
        chassis_len = self.first_rear_axle_pos + self.wheel_radius * 2
        parts.append(_create_cuboid((0, (overall_width - 1.0) / 2, self.frame_level_z - 0.2), 
                                   (chassis_len, 1.0, 0.2), 'dimgray', 'Рама тягача'))
        # Седло
        parts.append(_create_cuboid((self.saddle_pos - 0.5, (overall_width - 1.2) / 2, self.frame_level_z), 
                                   (1.0, 1.2, 0.05), 'darkslategrey', 'Седло'))
        # Колеса
        track_width = self.cab_width * 0.9
        y_left = (overall_width - track_width) / 2 - self.wheel_width / 2
        y_right = overall_width - y_left - self.wheel_width
        
        # Передние
        parts.extend(_create_cylinder((self.front_axle_pos, y_left + self.wheel_width/2, self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        parts.extend(_create_cylinder((self.front_axle_pos, y_right + self.wheel_width/2, self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        
        # Задние
        for i in range(self.num_rear_axles):
            axle_x = self.first_rear_axle_pos - (i * self.rear_axle_spacing)
            centers = [(axle_x, y, self.wheel_radius) for y in [y_left+self.wheel_width*1.5, y_left-self.wheel_width*0.5, y_right-self.wheel_width*0.5, y_right+self.wheel_width*1.5]]
            for center in centers: parts.extend(_create_cylinder(center, self.wheel_radius, self.wheel_width, 'y', name='Колесо'))

        return parts

class SemiTrailer:
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

    def get_components(self, x_offset, frame_level_z):
        """Возвращает список всех 3D компонентов полуприцепа со смещением."""
        parts = []
        # Кузов
        parts.append(_create_cuboid((x_offset, 0, frame_level_z), (self.length, self.width, self.height), 'lightcoral', 'Кузов'))
        # Рама
        parts.append(_create_cuboid((x_offset, (self.width - 1.0)/2, frame_level_z - 0.2), (self.length, 1.0, 0.2), 'dimgray', 'Рама прицепа'))
        # Колеса
        track_width = self.width * 0.9
        y_left = (self.width - track_width) / 2 - self.wheel_width / 2
        y_right = self.width - y_left - self.wheel_width
        
        first_axle_pos = x_offset + self.length - self.axle_pos_from_rear
        for i in range(self.num_axles):
            axle_x = first_axle_pos - (i * self.axle_spacing)
            centers = [(axle_x, y, self.wheel_radius) for y in [y_left+self.wheel_width*1.5, y_left-self.wheel_width*0.5, y_right-self.wheel_width*0.5, y_right+self.wheel_width*1.5]]
            for center in centers: parts.extend(_create_cylinder(center, self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
            
        return parts

class ArticulatedVehicle:
    def __init__(self, tractor: Tractor, trailer: SemiTrailer):
        self.tractor = tractor
        self.trailer = trailer

    def generate_figure(self):
        """Собирает тягач и прицеп в единую 3D модель."""
        # Логика сцепки
        trailer_start_x = self.tractor.saddle_pos - self.trailer.kingpin_offset
        
        tractor_parts = self.tractor.get_components(self.trailer.width)
        trailer_parts = self.trailer.get_components(trailer_start_x, self.tractor.frame_level_z)
        
        fig = go.Figure(data=tractor_parts + trailer_parts)
        
        fig.update_layout(
            title='Параметрическая 3D модель автопоезда',
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
