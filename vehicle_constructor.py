import plotly.graph_objects as go
import numpy as np

# --- Helper drawing functions ---

def _create_cuboid(origin, dimensions, color='lightblue', name='cuboid'):
    """Creates a cuboid for Plotly."""
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
    """Creates a cylinder for Plotly."""
    cx, cy, cz = center
    theta = np.linspace(0, 2 * np.pi, num_points)
    
    if axis == 'y':
        v = np.linspace(cy - length / 2, cy + length / 2, 2)
        theta_grid, v_grid = np.meshgrid(theta, v)
        x_grid, y_grid, z_grid = radius * np.cos(theta_grid) + cx, v_grid, radius * np.sin(theta_grid) + cz
    # ... (rest of the function is the same)
        
    colorscale = [[0, color], [1, color]]
    return go.Surface(x=x_grid, y=y_grid, z=z_grid, colorscale=colorscale, showscale=False, name=name, hoverinfo='name')

# --- Entity Classes ---

class Tractor:
    """Class representing a Tractor."""
    def __init__(self, brand="Tractor", model="Default", cab_length=2.2, cab_width=2.5, cab_height=2.8,
                 front_axle_pos=1.2, wheelbase=3.8, saddle_pos_from_rear_axle=0.5,
                 num_rear_axles=2, rear_axle_spacing=1.3, wheel_type='dual',
                 wheel_diameter=1.0, wheel_width=0.4):
        # ... (constructor is the same)
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
        self.frame_level_z = self.wheel_diameter * 1.1
        self.first_rear_axle_pos = self.front_axle_pos + self.wheelbase
        self.saddle_pos = self.first_rear_axle_pos + self.saddle_pos_from_rear_axle

    def get_unique_name(self):
        return f"{self.brand} {self.model} (Тягач)"

    def get_components(self, x_offset=0, y_offset=0, z_offset=0):
        """Returns a list of all 3D components for the tractor."""
        parts = []
        
        # TODO: Replace with loading a .gltf model of the cab
        # Cabin
        cab_y_offset = y_offset + (self.cab_width - self.cab_width) / 2 # Centering
        parts.append(_create_cuboid((x_offset, cab_y_offset, z_offset + self.frame_level_z), 
                                   (self.cab_length, self.cab_width, self.cab_height), 'royalblue', 'Кабина'))
        
        # Frame
        chassis_len = self.first_rear_axle_pos + (self.num_rear_axles -1) * self.rear_axle_spacing + self.saddle_pos_from_rear_axle + 0.5
        frame_width = 1.0
        parts.append(_create_cuboid((x_offset, y_offset + (self.cab_width - frame_width) / 2, z_offset + self.frame_level_z - 0.2), 
                                   (chassis_len, frame_width, 0.2), 'dimgray', 'Рама тягача'))
        # Saddle
        saddle_x_center = self.first_rear_axle_pos + self.saddle_pos_from_rear_axle
        saddle_width = 1.2
        parts.append(_create_cuboid((x_offset + saddle_x_center - 0.5, y_offset + (self.cab_width - saddle_width) / 2, z_offset + self.frame_level_z), 
                                   (1.0, saddle_width, 0.05), 'darkslategrey', 'Седло'))
        
        # Wheels
        y_left_center_single = y_offset + self.wheel_width / 2
        y_right_center_single = y_offset + self.cab_width - self.wheel_width / 2
        
        y_left_center_dual = y_offset + self.wheel_width
        y_right_center_dual = y_offset + self.cab_width - self.wheel_width

        # Front wheels
        parts.append(_create_cylinder((x_offset + self.front_axle_pos, y_left_center_single, z_offset + self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        parts.append(_create_cylinder((x_offset + self.front_axle_pos, y_right_center_single, z_offset + self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        
        # Rear wheels
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
    # ... (class is the same)
    """Class representing a Semi-Trailer."""
    def __init__(self, brand="Trailer", model="Default", length=13.6, width=2.55, height=2.7,
                 kingpin_offset=1.2, axle_pos_from_rear=2.5,
                 num_axles=3, axle_spacing=1.3,
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
        self.wheel_diameter = wheel_diameter
        self.wheel_width = wheel_width
        self.wheel_radius = self.wheel_diameter / 2

    def get_unique_name(self):
        return f"{self.brand} {self.model} (Прицеп)"

    def get_components(self, x_offset=0, y_offset=0, z_offset=0):
        """Returns a list of all 3D components for the semi-trailer."""
        parts = []

        # TODO: Replace with loading a .gltf model of the body (tented, tanker, etc.)
        # Body
        parts.append(_create_cuboid((x_offset, y_offset, z_offset), (self.length, self.width, self.height), 'lightcoral', 'Кузов'))
        # Frame
        frame_width = 1.0
        parts.append(_create_cuboid((x_offset, y_offset + (self.width - frame_width)/2, z_offset - 0.2), (self.length, frame_width, 0.2), 'dimgray', 'Рама прицепа'))
        
        # Wheels
        y_left_center = y_offset + self.wheel_width
        y_right_center = y_offset + self.width - self.wheel_width
        
        first_axle_pos = self.length - self.axle_pos_from_rear
        for i in range(self.num_axles):
            axle_x = x_offset + first_axle_pos - (i * self.axle_spacing)
            centers = [
                (axle_x, y_left_center - self.wheel_width/2, z_offset - 0.2 + self.wheel_radius),
                (axle_x, y_left_center + self.wheel_width/2, z_offset - 0.2 + self.wheel_radius),
                (axle_x, y_right_center - self.wheel_width/2, z_offset - 0.2 + self.wheel_radius),
                (axle_x, y_right_center + self.wheel_width/2, z_offset - 0.2 + self.wheel_radius)
            ]
            for center in centers: 
                parts.append(_create_cylinder(center, self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
            
        return parts
        
class Van:
    # ... (class is the same)
    """Class representing a Van."""
    def __init__(self, brand="Van", model="Default", body_length=6.0, body_width=2.4, body_height=2.2,
                 cab_length=2.0, front_axle_pos=1.2, wheelbase=4.0,
                 num_rear_axles=1, rear_axle_spacing=0,
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
        self.wheel_diameter = wheel_diameter
        self.wheel_width = wheel_width
        
        self.wheel_radius = self.wheel_diameter / 2
        self.frame_level_z = self.wheel_diameter * 1.1
    
    def get_unique_name(self):
        return f"{self.brand} {self.model} (Фургон)"

    def get_components(self, x_offset=0, y_offset=0, z_offset=0):
        """Returns a list of all 3D components for the van."""
        parts = []
        
        # TODO: Replace with loading a .gltf model of the van
        # Cabin
        parts.append(_create_cuboid((x_offset, y_offset, z_offset + self.frame_level_z),
                                   (self.cab_length, self.body_width, self.body_height), 'skyblue', 'Кабина фургона'))
        # Body
        parts.append(_create_cuboid((x_offset + self.cab_length, y_offset, z_offset + self.frame_level_z),
                                   (self.body_length, self.body_width, self.body_height), 'lightgrey', 'Кузов фургона'))
        # Frame
        chassis_len = self.cab_length + self.body_length
        frame_width = 1.0
        parts.append(_create_cuboid((x_offset, y_offset + (self.body_width - frame_width)/2, z_offset + self.frame_level_z - 0.2),
                                   (chassis_len, frame_width, 0.2), 'dimgray', 'Рама фургона'))
        # Wheels
        y_left_center = y_offset + self.wheel_width
        y_right_center = y_offset + self.body_width - self.wheel_width
        
        # Front wheels
        parts.append(_create_cylinder((x_offset + self.front_axle_pos, y_left_center, z_offset + self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        parts.append(_create_cylinder((x_offset + self.front_axle_pos, y_right_center, z_offset + self.wheel_radius), self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
        
        # Rear wheels
        first_rear_axle_pos = self.front_axle_pos + self.wheelbase
        for i in range(self.num_rear_axles):
            axle_x = first_rear_axle_pos + (i * self.rear_axle_spacing)
            centers = [
                (x_offset + axle_x, y_left_center - self.wheel_width/2, z_offset + self.wheel_radius),
                (x_offset + axle_x, y_left_center + self.wheel_width/2, z_offset + self.wheel_radius),
                (x_offset + axle_x, y_right_center - self.wheel_width/2, z_offset + self.wheel_radius),
                (x_offset + axle_x, y_right_center + self.wheel_width/2, z_offset + self.wheel_radius)
            ]
            for center in centers: 
                parts.append(_create_cylinder(center, self.wheel_radius, self.wheel_width, 'y', name='Колесо'))
            
        return parts

# --- Scene Assembler Class ---
class Scene:
    """Class for assembling and displaying various transport entities."""
    def __init__(self):
        self.components = []

    def add(self, vehicle, x=0, y=0, z=0):
        """Universal method for adding any vehicle to the scene."""
        if vehicle:
            self.components.extend(vehicle.get_components(x, y, z))

    def add_articulated_vehicle(self, tractor, trailer):
        """Adds a tractor-trailer combination to the scene."""
        if tractor and trailer:
            # Calculate the coupling point
            trailer_start_x = tractor.saddle_pos - trailer.kingpin_offset
            # Center the tractor relative to the wider trailer for aesthetics
            y_offset_tractor = (trailer.width - tractor.cab_width) / 2
            
            self.add(tractor, y_offset=y_offset_tractor)
            self.add(trailer, x=trailer_start_x, z=tractor.frame_level_z)

    def generate_figure(self):
        """Assembles all added components into a single 3D model."""
        if not self.components:
            # Return an empty scene if there are no components
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

