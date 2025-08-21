import numpy as np
import plotly.graph_objects as go
from itertools import permutations
from operator import itemgetter
import re
from colorsys import hls_to_rgb
import math
from decimal import Decimal, getcontext
import traceback
import copy

# =====================================================================================
# БЛОК УТИЛИТ ДЛЯ ПРОВЕРКИ ПОЛЬЗОВАТЕЛЬСКОГО ВВОДА (INPUT_VALIDATION_UTILS)
# =====================================================================================

def get_validated_float(prompt, positive_only=True, allow_zero=False):
    """Запрашивает у пользователя ввод десятичного числа, обрабатывая ошибки."""
    while True:
        user_input = input(prompt).strip()
        if user_input.lower() == 'q': return None
        if ',' in user_input:
            user_input = user_input.replace(',', '.')
            print(f"INFO: Запятая была автоматически заменена на точку: '{user_input}'")
        try:
            value = float(user_input)
            if positive_only:
                if allow_zero and value < 0:
                    print("ОШИБКА: Пожалуйста, введите положительное число или ноль.")
                    continue
                elif not allow_zero and value <= 0:
                    print("ОШИБКА: Пожалуйста, введите положительное число больше нуля.")
                    continue
            return value
        except ValueError:
            print("ОШИБКА: Некорректный ввод. Пожалуйста, введите число (например, '1.5'). Для выхода введите 'q'.")

def get_validated_int(prompt, positive_only=True):
    """Запрашивает у пользователя ввод целого числа, обрабатывая ошибки."""
    while True:
        user_input = input(prompt).strip()
        if user_input.lower() == 'q': return None
        try:
            value = int(user_input)
            if positive_only and value <= 0:
                print("ОШИБКА: Пожалуйста, введите положительное число больше нуля.")
                continue
            return value
        except ValueError:
            print("ОШИБКА: Некорректный ввод. Пожалуйста, введите целое число. Для выхода введите 'q'.")

def get_validated_choice(prompt, options):
    """Запрашивает у пользователя выбор из списка опций."""
    print(prompt)
    str_options = {str(k): v for k, v in options.items()}
    for key, value in str_options.items(): print(f"  {key} - {value}")
    while True:
        choice = input("Ваш выбор ('q' для выхода): ").strip()
        if choice.lower() == 'q': return None
        if choice in str_options: return choice
        else: print(f"ОШИБКА: Некорректный выбор. Пожалуйста, введите одно из следующих чисел: {', '.join(str_options.keys())}.")

def pre_check_cargo(item, available_units):
    """Проверяет, может ли груз поместиться хотя бы в одну из доступных транспортных единиц."""
    can_fit_anywhere = False
    for unit in available_units:
        # Для контейнеров и не-ТС max_weight - это полезная нагрузка
        # Для ТС max_weight - это полная масса, поэтому сравниваем с (полная масса - снаряженная масса)
        payload = unit['max_weight']
        if 'curb_axle_loads' in unit:
            curb_weight = sum(unit['curb_axle_loads'])
            payload = unit['max_weight'] - curb_weight
        if item['вес'] > payload: continue
        item_dims_dict = item['размеры_исходные']
        if item['форма'] == 'box': item_dims = sorted(list(item_dims_dict.values()))
        elif item['форма'] == 'cylinder': item_dims = sorted([item_dims_dict['diameter'], item_dims_dict['diameter'], item_dims_dict['height']])
        else: item_dims = []
        unit_dims = sorted([unit['length'], unit['width'], unit['height']])
        if all(item_dim <= unit_dim for item_dim, unit_dim in zip(item_dims, unit_dims)):
            can_fit_anywhere = True
            break
    if not can_fit_anywhere:
        print("\n" + "="*50 + f"\nПРЕДУПРЕЖДЕНИЕ: Груз '{item['наименование']}' слишком большой или тяжелый!\n" + "Он не поместится ни в одну из выбранных транспортных единиц.\n" + "="*50 + "\n")
        return False
    return True

def check_pallet_fit(item, pallet_info, allowed_orientations=None):
    """Проверяет, помещается ли груз на поддон по весу и габаритам."""
    if item['вес'] > pallet_info['max_weight']:
        print(f"\nОШИБКА: Вес одного места груза ({item['вес']} кг) превышает грузоподъемность поддона ({pallet_info['max_weight']} кг).")
        return False
    p_l, p_w = pallet_info['length'], pallet_info['width']
    
    if allowed_orientations is None:
        if item['форма'] == 'box':
            l, w, h = item['размеры_исходные'].values()
            allowed_orientations = list(set(permutations([l, w, h])))
        elif item['форма'] == 'cylinder':
            d = item['размеры_исходные']['diameter']
            allowed_orientations = [(d, d, item['размеры_исходные']['height'])]
    
    can_fit = False
    for d1, d2, d3 in allowed_orientations:
        if (d1 <= p_l and d2 <= p_w) or (d1 <= p_w and d2 <= p_l):
            can_fit = True
            break
    
    if not can_fit:
        print(f"\nОШИБКА: Груз с габаритами ({item['размеры_исходные']}) не помещается на основание поддона ({p_l}x{p_w}) ни в одной из разрешенных ориентаций.")
        return False
        
    return True

# --- УТИЛИТАРНЫЕ ФУНКЦИИ ---
def get_item_volume(item):
    """Возвращает объем предмета."""
    dims = item.get('dims', [])
    if not dims and 'размеры_исходные' in item:
        if item.get('форма') == 'box' or item.get('форма') == 'pallet':
            dims = [item['размеры_исходные']['length'], item['размеры_исходные']['width'], item['размеры_исходные']['height']]
        elif item.get('форма') == 'cylinder':
            r = item['размеры_исходные']['diameter'] / 2
            h = item['размеры_исходные']['height']
            return math.pi * (r**2) * h
    if not dims: return 0
    if item.get('форма') == 'box' or item.get('форма') == 'pallet':
        return dims[0] * dims[1] * dims[2]
    elif item.get('форма') == 'cylinder':
        orig_dims = item['размеры_исходные']
        return math.pi * (orig_dims['diameter'] / 2)**2 * orig_dims['height']
    return 0

# --- БАЗЫ ДАННЫХ ---
TRANSPORT_UNIT_DB = {
    'containers': {
        '20ft': {'name':'20-футовый стандартный контейнер', 'length':5.898, 'width':2.352, 'height':2.393, 'max_weight':28200},
        '40ft': {'name':'40-футовый стандартный контейнер', 'length':12.032, 'width':2.352, 'height':2.393, 'max_weight':28700},
        '40ft_hc': {'name':'40-футовый увеличенный контейнер (HC)', 'length':12.032, 'width':2.352, 'height':2.698, 'max_weight':28700},
        'custom': {'name': 'Пользовательский контейнер'}
    },
    'vehicles': {
        'standard_trailer': {'name':'Стандартный-трейлер (Еврофура)', 'length':13.6, 'width':2.45, 'height':2.7, 'max_weight':40000, 'tractor_curb_weight': 7000, 'trailer_curb_weight': 8000, 'curb_axle_loads': [6000, 4500, 2500, 2500, 2500], 'axles': 5, 'wheelbase': 3.8, 'track_width_front': 2.0, 'track_width_rear': 1.8, 'axle_positions': [1.5, 3.8, 12.7, 14.0, 15.3], 'wheel_type': 'dual', 'cg_height_empty': 1.5, 'saddle_position_x': 3.6, 'saddle_height': 1.25, 'kingpin_setback': 1.2},
        'van': {'name': 'Фургон (LCV)', 'length': 4.2, 'width': 2.1, 'height': 2.2, 'max_weight': 3500, 'curb_axle_loads': [1250, 1250], 'axles': 2, 'wheelbase': 3.5, 'track_width_front': 1.8, 'track_width_rear': 1.8, 'axle_positions': [0.5, 3.0], 'wheel_type': 'dual', 'cg_height_empty': 1.2},
        'custom': {'name': 'Пользовательский автомобиль'}
    },
    'russian_trucks': {
        'solo_2_axle': {'name': 'Одиночный 2-осный автомобиль (РФ)', 'length': 7.0, 'width': 2.5, 'height': 3.0, 'max_weight': 18000, 'curb_axle_loads': [3200, 4800], 'axles': 2, 'wheelbase': 4.0, 'track_width_front': 2.0, 'track_width_rear': 2.0, 'axle_positions': [1.0, 5.0], 'wheel_type': 'dual', 'cg_height_empty': 1.4},
        'solo_3_axle': {'name': 'Одиночный 3-осный автомобиль (РФ)', 'length': 9.0, 'width': 2.5, 'height': 3.0, 'max_weight': 25000, 'curb_axle_loads': [3000, 3500, 3500], 'axles': 3, 'wheelbase': 6.0, 'track_width_front': 2.0, 'track_width_rear': 2.0, 'axle_positions': [1.0, 4.0, 5.3], 'wheel_type': 'dual', 'cg_height_empty': 1.5},
        'solo_4_axle': {'name': 'Одиночный 4-осный автомобиль (РФ)', 'length': 11.0, 'width': 2.5, 'height': 3.0, 'max_weight': 32000, 'curb_axle_loads': [3000, 3000, 3000, 3000], 'axles': 4, 'wheelbase': 7.0, 'track_width_front': 2.0, 'track_width_rear': 2.0, 'axle_positions': [1.0, 3.0, 5.0, 6.3], 'wheel_type': 'dual', 'cg_height_empty': 1.5},
        'artic_3_axle_2_1': {'name': 'Автопоезд седельный 3-осный (2+1) (РФ)', 'length': 13.6, 'width': 2.45, 'height': 2.7, 'max_weight': 28000, 'tractor_curb_weight': 7000, 'trailer_curb_weight': 3000, 'curb_axle_loads': [6000, 4000, 3000], 'axles': 3, 'wheelbase': 3.8, 'track_width_front': 2.0, 'track_width_rear': 1.8, 'axle_positions': [1.5, 3.8, 14.0], 'wheel_type': 'dual', 'cg_height_empty': 1.5, 'saddle_position_x': 3.6, 'saddle_height': 1.3, 'kingpin_setback': 1.2},
        'artic_5_axle_2_3': {'name': 'Автопоезд седельный 5-осный (2+3) (РФ)', 'length':13.6, 'width':2.45, 'height':2.7, 'max_weight':40000, 'tractor_curb_weight': 7000, 'trailer_curb_weight': 8000, 'curb_axle_loads': [6000, 4500, 2500, 2500, 2500], 'axles': 5, 'wheelbase': 3.8, 'track_width_front': 2.0, 'track_width_rear': 1.8, 'axle_positions': [1.5, 3.8, 12.7, 14.0, 15.3], 'wheel_type': 'dual', 'cg_height_empty': 1.5, 'saddle_position_x': 3.6, 'saddle_height': 1.25, 'kingpin_setback': 1.2},
        'artic_6_axle_3_3': {'name': 'Автопоезд седельный 6-осный (3+3) (РФ)', 'length': 13.6, 'width': 2.45, 'height': 2.7, 'max_weight': 44000, 'tractor_curb_weight': 7500, 'trailer_curb_weight': 8500, 'curb_axle_loads': [5500, 4500, 4500, 2500, 2500, 2500], 'axles': 6, 'wheelbase': 3.8, 'track_width_front': 2.0, 'track_width_rear': 1.8, 'axle_positions': [1.5, 2.8, 4.1, 12.7, 14.0, 15.3], 'wheel_type': 'dual', 'cg_height_empty': 1.6, 'saddle_position_x': 3.8, 'saddle_height': 1.25, 'kingpin_setback': 1.2},
    }
}

PALLET_DATABASE = {
    'euro_1200_800': {'name':'Европейский поддон 1.2x0.8', 'length':1.2, 'width':0.8, 'cargo_height':2.0, 'depth':0.1, 'max_weight':1500, 'self_weight':20},
    'euro_1200_1000': {'name':'Европейский поддон 1.2x1.0', 'length':1.2, 'width':1.0, 'cargo_height':2.0, 'depth':0.1, 'max_weight':1500, 'self_weight':25},
    'euro_1200_1200': {'name':'Европейский поддон 1.2x1.2', 'length':1.2, 'width':1.2, 'cargo_height':2.0, 'depth':0.1, 'max_weight':1500, 'self_weight':30},
    'euro_half': {'name':'Европейский поддон (половина) 0.6x0.8', 'length':0.6, 'width':0.8, 'cargo_height':2.0, 'depth':0.1, 'max_weight':1300, 'self_weight':10},
    'euro_plastic': {'name':'Европейский пластиковый поддон 1.2x0.8', 'length':1.2, 'width':0.8, 'cargo_height':2.0, 'depth':0.1, 'max_weight':1300, 'self_weight':8},
    'us_pallet': {'name':'Американский поддон 1.2x1.0', 'length':1.219, 'width':1.016, 'cargo_height':2.0, 'depth':0.1, 'max_weight':750, 'self_weight':20},
    'custom_pallet': {'name':'Поддон по индивидуальному заказу', 'length':1.2, 'width':0.8, 'cargo_height':2.0, 'depth':0.1, 'max_weight':1500, 'self_weight':20}
}

AXLE_LOAD_REGULATIONS = {
    'total_weight_by_axles': {
        2: 18000, 3: 25000, 4: 32000, 5: 38000, 6: 44000, 7: 44000
    },
    'axle_group_limits': {
        'single': { 'dual': {(0, float('inf')): 10000} },
        'double': { 'dual': { (0, 1.0): 13000, (1.0, 1.3): 16000, (1.3, 1.8): 18000, (1.8, 2.5): 20000 }},
        'triple': { 'dual': { (0, 1.0): 18000, (1.0, 1.3): 21000, (1.3, 1.8): 24000, (1.8, 2.5): 26000 }},
        'quad_plus': {
            'single': { (0, 1.0): 16000, (1.0, 1.3): 18000, (1.3, 1.8): 20000, (1.8, 2.5): 22000 },
            'dual': { (0, float('inf')): 26000 }
        }
    }
}

getcontext().prec = 20

# --- КЛАССЫ И ЛОГИКА УПАКОВКИ ---

class AxleLoadCalculator:
    """
    Универсальный класс для расчета осевых нагрузок.
    Поддерживает 2D, 3D (упрощенный) и 3D (для автопоездов) режимы.
    """
    def __init__(self, vehicle_params):
        self.params = {}
        for k, v in vehicle_params.items():
            if k == 'axles':
                self.params[k] = int(v)
            elif k == 'axle_positions' or k == 'curb_axle_loads':
                self.params[k] = [Decimal(str(p)) for p in v]
            elif isinstance(v, (int, float)):
                self.params[k] = Decimal(str(v))
            else:
                self.params[k] = v
        self.params['wheel_type'] = vehicle_params.get('wheel_type', 'dual')

    def get_loads(self, placed_items, effective_curb_weight, mode='2d'):
        """
        Основной метод-диспетчер для вызова нужной логики расчета.
        mode: '2d', '3d_simple', '3d_articulated'
        """
        is_articulated = 'saddle_position_x' in self.params
        
        if mode == '2d':
            if is_articulated:
                # Используем 3D-расчет для автопоезда, но без учета Y и Z
                return self._calculate_loads_3d_articulated(placed_items, is_2d=True)
            else:
                loads_2d = self._calculate_loads_2d(placed_items, effective_curb_weight)
                return {
                    'total_axle_loads': loads_2d['loads'],
                    'cg_cargo': loads_2d['cg_cargo'],
                    'wheel_loads': {}
                }
        elif mode == '3d_articulated':
            return self._calculate_loads_3d_articulated(placed_items)
        elif mode == '3d_simple':
            return self._calculate_loads_3d_simple(placed_items)
        else: # Fallback
            loads_2d = self._calculate_loads_2d(placed_items, effective_curb_weight)
            return {
                'total_axle_loads': loads_2d['loads'],
                'cg_cargo': loads_2d['cg_cargo'],
                'wheel_loads': {}
            }

    def _calculate_3d_cg(self, items, is_2d=False):
        """Рассчитывает 3D-центр тяжести для набора предметов."""
        total_weight = sum(Decimal(str(item['вес'])) for item in items)
        if total_weight == 0: return {'x': Decimal('0'), 'y': Decimal('0'), 'z': Decimal('0')}
        moment_x = sum((Decimal(str(item['position'][0])) + Decimal(str(item['dims'][0])) / 2) * Decimal(str(item['вес'])) for item in items)
        
        if is_2d:
            # В 2D режиме считаем, что груз идеально сбалансирован по поперечной оси
            moment_y = (self.params.get('width', Decimal('2.4')) / 2) * total_weight # Fallback width
            moment_z = Decimal('0') # Высота не учитывается
        else:
            moment_y = sum((Decimal(str(item['position'][1])) + Decimal(str(item['dims'][1])) / 2) * Decimal(str(item['вес'])) for item in items)
            moment_z = sum((Decimal(str(item['position'][2])) + Decimal(str(item['dims'][2])) / 2) * Decimal(str(item['вес'])) for item in items)
        return {
            'x': moment_x / total_weight,
            'y': moment_y / total_weight,
            'z': moment_z / total_weight
        }

    def _calculate_wheel_loads(self, total_axle_loads, cg_cargo_rel, total_cargo_weight):
        """Вспомогательная функция для расчета нагрузок на левые/правые колеса."""
        wheel_loads = {}
        num_axles = len(total_axle_loads)
        
        l_y = cg_cargo_rel['y'] - (self.params['width'] / 2)
        h_g = cg_cargo_rel['z'] # Это высота ЦТ груза от пола кузова
        
        roll_moment = total_cargo_weight * l_y
        
        total_load_on_vehicle = sum(total_axle_loads)
        if total_load_on_vehicle <= 0: return {}
        for i in range(num_axles):
            axle_num = i + 1
            track_width = self.params['track_width_front'] if i == 0 else self.params['track_width_rear']
            
            # Момент крена распределяется пропорционально осевой нагрузке
            moment_share = roll_moment * (total_axle_loads[i] / total_load_on_vehicle)
            # Перераспределение нагрузки из-за высоты ЦТ (упрощенно)
            load_transfer_from_height = (moment_share * h_g) / track_width if track_width > 0 else 0
            
            wheel_loads[f'P{axle_num}_left'] = float(total_axle_loads[i] / 2 - load_transfer_from_height)
            wheel_loads[f'P{axle_num}_right'] = float(total_axle_loads[i] / 2 + load_transfer_from_height)
        return wheel_loads

    def _calculate_loads_3d_simple(self, placed_items):
        """Упрощенный 3D расчет (для одиночных ТС)."""
        num_axles = int(self.params.get('axles', 0))
        total_cargo_weight = sum(Decimal(str(item['вес'])) for item in placed_items)
        
        final_axle_loads = [Decimal(str(l)) for l in self.params['curb_axle_loads']]
        cg_cargo_rel = self._calculate_3d_cg(placed_items)
        if total_cargo_weight > 0:
            cargo_cog_x = cg_cargo_rel['x']
            segment_found = False
            for i in range(num_axles - 1):
                pos_curr = self.params['axle_positions'][i]
                pos_next = self.params['axle_positions'][i+1]
                if pos_curr <= cargo_cog_x <= pos_next:
                    if pos_next - pos_curr != 0:
                        final_axle_loads[i] += total_cargo_weight * (pos_next - cargo_cog_x) / (pos_next - pos_curr)
                        final_axle_loads[i+1] += total_cargo_weight * (cargo_cog_x - pos_curr) / (pos_next - pos_curr)
                    else:
                        final_axle_loads[i] += total_cargo_weight / 2
                        final_axle_loads[i+1] += total_cargo_weight / 2
                    segment_found = True
                    break
            if not segment_found:
                if cargo_cog_x < self.params['axle_positions'][0]: final_axle_loads[0] += total_cargo_weight
                else: final_axle_loads[-1] += total_cargo_weight
        wheel_loads = self._calculate_wheel_loads(final_axle_loads, cg_cargo_rel, total_cargo_weight)
        
        return {
            'total_axle_loads': [float(l) for l in final_axle_loads],
            'cg_cargo': {k: float(v) for k, v in cg_cargo_rel.items()},
            'wheel_loads': wheel_loads
        }

    def _calculate_loads_3d_articulated(self, placed_items, is_2d=False):
        """Точный 3D расчет для автопоездов."""
        saddle_x = self.params['saddle_position_x']
        tractor_axle_indices = [i for i, pos in enumerate(self.params['axle_positions']) if pos <= saddle_x]
        trailer_axle_indices = [i for i, pos in enumerate(self.params['axle_positions']) if pos > saddle_x]
        cg_cargo_rel = self._calculate_3d_cg(placed_items, is_2d)
        total_cargo_weight = sum(Decimal(str(item['вес'])) for item in placed_items)
        if total_cargo_weight == 0:
            return {
                'total_axle_loads': [float(l) for l in self.params['curb_axle_loads']],
                'cg_cargo': {'x':0,'y':0,'z':0}, 'wheel_loads': {}
            }
        kingpin_setback = self.params.get('kingpin_setback', Decimal('1.0'))
        cargo_space_offset_x = self.params.get('saddle_position_x') - kingpin_setback
        cg_cargo_abs_x = cargo_space_offset_x + cg_cargo_rel['x']
        trailer_axle_positions = [self.params['axle_positions'][i] for i in trailer_axle_indices]
        trailer_bogie_center_x = sum(trailer_axle_positions) / len(trailer_axle_positions)
        
        lever_arm_total = trailer_bogie_center_x - saddle_x
        F_kingpin = total_cargo_weight * (trailer_bogie_center_x - cg_cargo_abs_x) / lever_arm_total if lever_arm_total != 0 else total_cargo_weight / 2
        F_trailer_axles_total = total_cargo_weight - F_kingpin
        final_axle_loads = [Decimal(str(l)) for l in self.params['curb_axle_loads']]
        
        if trailer_axle_indices:
            load_per_trailer_axle = F_trailer_axles_total / len(trailer_axle_indices)
            for i in trailer_axle_indices:
                final_axle_loads[i] += load_per_trailer_axle
        tractor_axle_positions = [self.params['axle_positions'][i] for i in tractor_axle_indices]
        if tractor_axle_indices:
            # Распределяем нагрузку от седла на оси тягача
            front_axle_pos = tractor_axle_positions[0]
            rear_tractor_axles_pos = tractor_axle_positions[1:]
            
            if rear_tractor_axles_pos:
                rear_bogie_center_x = sum(rear_tractor_axles_pos) / len(rear_tractor_axles_pos)
                tractor_span = rear_bogie_center_x - front_axle_pos
                
                if tractor_span > 0:
                    F_rear_bogie = F_kingpin * (saddle_x - front_axle_pos) / tractor_span
                    F_front_axle = F_kingpin - F_rear_bogie
                    
                    final_axle_loads[tractor_axle_indices[0]] += F_front_axle
                    
                    # Распределяем нагрузку на заднюю тележку тягача
                    if len(rear_tractor_axles_pos) > 0:
                        load_per_rear_axle = F_rear_bogie / len(rear_tractor_axles_pos)
                        for i in tractor_axle_indices[1:]:
                            final_axle_loads[i] += load_per_rear_axle
                else: # Если оси в одной точке
                    load_per_axle = F_kingpin / len(tractor_axle_indices)
                    for i in tractor_axle_indices:
                        final_axle_loads[i] += load_per_axle
            else: # Только одна ось у тягача (нереалистично, но для полноты)
                final_axle_loads[tractor_axle_indices[0]] += F_kingpin
        wheel_loads = {} if is_2d else self._calculate_wheel_loads(final_axle_loads, cg_cargo_rel, total_cargo_weight)
        
        return {
            'total_axle_loads': [float(l) for l in final_axle_loads],
            'cg_cargo': {k: float(v) for k, v in cg_cargo_rel.items()},
            'wheel_loads': wheel_loads
        }

    def _calculate_loads_2d(self, placed_items, effective_curb_weight):
        """Расчет нагрузок по 2D модели для ОДИНОЧНЫХ ТС."""
        total_cargo_weight = sum(Decimal(str(item['вес'])) for item in placed_items)
        default_total_curb_load = sum(self.params['curb_axle_loads'])
        scaling_factor = effective_curb_weight / default_total_curb_load if effective_curb_weight is not None and default_total_curb_load > 0 else Decimal('1.0')
        axle_loads = [load * scaling_factor for load in self.params['curb_axle_loads']]
        if total_cargo_weight == 0:
            return {'loads': [float(l) for l in axle_loads], 'cg_cargo': {'x':0, 'y':0, 'z':0}}
        cg_cargo_rel = self._calculate_3d_cg(placed_items, is_2d=True)
        cargo_cog_x_abs = cg_cargo_rel['x'] 
        num_axles = len(self.params['axle_positions'])
        
        if num_axles >= 2:
            segment_found = False
            for i in range(num_axles - 1):
                pos_curr, pos_next = self.params['axle_positions'][i], self.params['axle_positions'][i+1]
                if pos_curr <= cargo_cog_x_abs <= pos_next:
                    if pos_next - pos_curr != 0:
                        axle_loads[i] += total_cargo_weight * (pos_next - cargo_cog_x_abs) / (pos_next - pos_curr)
                        axle_loads[i+1] += total_cargo_weight * (cargo_cog_x_abs - pos_curr) / (pos_next - pos_curr)
                    else:
                        axle_loads[i] += total_cargo_weight / 2
                        axle_loads[i+1] += total_cargo_weight / 2
                    segment_found = True
                    break
            if not segment_found:
                if cargo_cog_x_abs < self.params['axle_positions'][0]: axle_loads[0] += total_cargo_weight
                else: axle_loads[-1] += total_cargo_weight
        elif num_axles == 1:
            axle_loads[0] += total_cargo_weight
        return {'loads': [float(l) for l in axle_loads], 'cg_cargo': {k: float(v) for k, v in cg_cargo_rel.items()}}

    def _identify_axle_groups(self):
        """Определяет группы осей на основе близости (макс. 2.5м расстояние для группы в правилах РФ)."""
        axle_groups = []
        if not self.params['axle_positions']: return []
        current_group = [0]
        for i in range(1, len(self.params['axle_positions'])):
            dist = self.params['axle_positions'][i] - self.params['axle_positions'][i-1]
            if dist <= Decimal('2.5'):
                current_group.append(i)
            else:
                axle_groups.append(current_group)
                current_group = [i]
        axle_groups.append(current_group)
        return axle_groups

    def _get_axle_group_limit(self, group_axle_indices, effective_distance_between_axles, wheel_type):
        """
        Получает нормативное ограничение для группы осей и возвращает ограничение НА ОСЬ.
        """
        num_axles_in_group = len(group_axle_indices)
        group_total_limit = float('inf')
        if num_axles_in_group == 1:
            rule_set = AXLE_LOAD_REGULATIONS['axle_group_limits']['single'][wheel_type]
        elif num_axles_in_group == 2:
            rule_set = AXLE_LOAD_REGULATIONS['axle_group_limits']['double'][wheel_type]
        elif num_axles_in_group == 3:
            rule_set = AXLE_LOAD_REGULATIONS['axle_group_limits']['triple'][wheel_type]
        else:
            rule_set = AXLE_LOAD_REGULATIONS['axle_group_limits']['quad_plus'][wheel_type]
        for (min_dist, max_dist), limit in rule_set.items():
            if min_dist <= effective_distance_between_axles < max_dist:
                group_total_limit = limit
                break
        
        return group_total_limit / num_axles_in_group if num_axles_in_group > 0 else float('inf')

    def check_axle_load_compliance(self, placed_items, effective_curb_weight, total_vehicle_gvw_limit, calculation_mode='2d', tolerance_percent=0.0):
        """
        Проверяет соответствие осевых нагрузок и общего веса нормам.
        """
        total_cargo_weight = sum(Decimal(str(item['вес'])) for item in placed_items)
        total_vehicle_weight = effective_curb_weight + total_cargo_weight
        
        if not placed_items:
            return {'is_compliant': True, 'reason': "СООТВЕТСТВУЕТ", 'details': {}}
        compliance_details = {'total_weight_exceeded': False, 'individual_axle_exceeded': {}, 'axle_deviations': {}}
        is_overall_compliant = True
        if total_vehicle_weight > total_vehicle_gvw_limit * (1 + Decimal(str(tolerance_percent)) / 100):
            compliance_details['total_weight_exceeded'] = True
            is_overall_compliant = False
        loads_info = self.get_loads(placed_items, effective_curb_weight, mode=calculation_mode)
        current_axle_loads = loads_info['total_axle_loads']
        axle_groups = self._identify_axle_groups()
        axle_limits = {}
        for group_indices in axle_groups:
            effective_distance = 0.0
            if len(group_indices) > 1:
                effective_distance = min(float(self.params['axle_positions'][group_indices[i+1]] - self.params['axle_positions'][group_indices[i]]) for i in range(len(group_indices) - 1))
            
            per_axle_limit = self._get_axle_group_limit(group_indices, effective_distance, self.params['wheel_type'])
            for idx in group_indices:
                axle_limits[idx] = per_axle_limit
        
        for idx, current_load in enumerate(current_axle_loads):
            limit = axle_limits.get(idx, self._get_axle_group_limit([idx], 0, self.params['wheel_type']))
            limit_decimal = Decimal(str(limit))
            if Decimal(str(current_load)) > limit_decimal * (1 + Decimal(str(tolerance_percent)) / 100):
                compliance_details['individual_axle_exceeded'][idx] = True
                is_overall_compliant = False
            
            deviation_kg = Decimal(str(current_load)) - limit_decimal
            compliance_details['axle_deviations'][idx] = {
                'deviation_kg': float(deviation_kg),
                'deviation_percent': float(deviation_kg / limit_decimal * 100) if limit_decimal > 0 else 0,
                'limit_kg': float(limit_decimal)
            }
        
        reason = "СООТВЕТСТВУЕТ"
        if compliance_details['total_weight_exceeded']: reason = "ПРЕВЫШЕНА_ОБЩАЯ_МАССА"
        elif compliance_details['individual_axle_exceeded']: reason = "ПРЕВЫШЕНА_ОСЬ"
        return {'is_compliant': is_overall_compliant, 'reason': reason, 'details': compliance_details}

    def _evaluate_axle_load_score(self, placed_items, effective_curb_weight, total_vehicle_gvw_limit, calculation_mode):
        """
        Оценивает "качество" распределения осевой нагрузки. Чем ниже балл, тем лучше.
        """
        compliance_result = self.check_axle_load_compliance(placed_items, effective_curb_weight, total_vehicle_gvw_limit, calculation_mode)
        if not compliance_result['is_compliant']:
            return 1_000_000_000
        score = 0.0
        total_cargo_weight = sum(Decimal(str(item['вес'])) for item in placed_items)
        available_capacity = total_vehicle_gvw_limit - effective_curb_weight
        if available_capacity > 0:
            score -= float(total_cargo_weight / available_capacity) * 1000
        # ИСПРАВЛЕНИЕ: 'calculation_model' заменено на 'calculation_mode'
        loads_info = self.get_loads(placed_items, effective_curb_weight, mode=calculation_mode)
        current_axle_loads = loads_info['total_axle_loads']
        
        if len(current_axle_loads) > 1:
            mean_load = sum(current_axle_loads) / len(current_axle_loads)
            variance = sum((load - mean_load)**2 for load in current_axle_loads) / len(current_axle_loads)
            score += variance / 1000
        return score

class PalletizedGroup:
    """Класс для группировки предметов на поддонах."""
    def __init__(self, items, pallet_info):
        """Инициализирует группу поддонов с предметами и информацией о поддоне."""
        self.items, self.pallet_info, self.palletized_items = items, pallet_info, []
        if not self.items: return
        self.base_item = self.items[0]
        self._palletize()

    def _palletize(self):
        """Выполняет процесс паллетизации предметов."""
        item_h = self.base_item['размеры_исходные']['height']
        item_weight = self.base_item['вес']
        items_per_layer, best_layout = self._calculate_best_layer()
        if items_per_layer == 0:
            for item in self.items: self.palletized_items.append(item)
            return
        layers_by_pallet_h = float('inf')
        if item_h > 0: layers_by_pallet_h = math.floor(self.pallet_info['cargo_height'] / item_h)
        user_h_limit = self.base_item['constraints'].get('max_stack_height', float('inf'))
        layers_by_user_h = float('inf')
        if user_h_limit != float('inf') and item_h > 0: layers_by_user_h = math.floor(user_h_limit / item_h)
        layers_by_user_layers = self.base_item['constraints'].get('max_stack_layers', float('inf'))
        max_layers_by_height = min(layers_by_pallet_h, layers_by_user_h, layers_by_user_layers)
        if max_layers_by_height == float('inf') or max_layers_by_height < 1: max_layers_by_height = 1
        else: max_layers_by_height = int(max_layers_by_height)
        
        max_items_by_geometry = items_per_layer * max_layers_by_height
        
        max_items_by_weight = float('inf')
        if item_weight > 0: max_items_by_weight = math.floor(self.pallet_info['max_weight'] / item_weight)
        items_per_full_pallet = int(min(max_items_by_geometry, max_items_by_weight))
        if items_per_full_pallet <= 0:
            for item in self.items: self.palletized_items.append(item)
            return
        num_full_pallets = len(self.items) // items_per_full_pallet
        for i in range(num_full_pallets):
            start_index = i * items_per_full_pallet
            end_index = start_index + items_per_full_pallet
            layers_for_full = math.ceil(items_per_full_pallet / items_per_layer)
            self._create_meta_item(self.items[start_index : end_index], layers_for_full, best_layout)
        remaining_items_count = len(self.items) % items_per_full_pallet
        if remaining_items_count > 0:
            start_index = num_full_pallets * items_per_full_pallet
            layers_for_remaining = math.ceil(remaining_items_count / items_per_layer)
            self._create_meta_item(self.items[start_index:], layers_for_remaining, best_layout)

    def _create_meta_item(self, packed_items, num_layers, layout):
        """Создает мета-предмет, представляющий паллетизированную группу."""
        if not packed_items: return
        item_h = self.base_item['размеры_исходные']['height']
        if item_h == 0 and num_layers > 0: total_h = self.pallet_info['depth']
        else: total_h = (num_layers * item_h) + self.pallet_info['depth']
        total_w = self.pallet_info['self_weight'] + (len(packed_items) * self.base_item['вес'])
        
        # Наследуем ограничения от базового предмета, но переопределяем/добавляем ограничения самого поддона
        pallet_constraints = self.base_item['constraints'].copy()
        
        # --- Ограничение по нагрузке ---
        # Физический предел нагрузки на поддон
        pallet_physical_load_limit = self.pallet_info['max_weight']
        if 'max_stack_load' in pallet_constraints:
            # Если пользователь определил ограничение для груза, выбираем самое строгое
            pallet_constraints['max_stack_load'] = min(pallet_constraints['max_stack_load'], pallet_physical_load_limit)
        else:
            # Иначе, используем ограничение поддона
            pallet_constraints['max_stack_load'] = pallet_physical_load_limit
        # --- Ограничение по высоте ---
        # Физический предел высоты штабеля, начинающегося с этого поддона
        pallet_physical_height_limit = self.pallet_info['cargo_height'] + self.pallet_info['depth']
        if 'max_stack_height' in pallet_constraints:
            # Если пользователь определил ограничение для груза, выбираем самое строгое
            pallet_constraints['max_stack_height'] = min(pallet_constraints['max_stack_height'], pallet_physical_height_limit)
        else:
            # Иначе, используем ограничение поддона
            pallet_constraints['max_stack_height'] = pallet_physical_height_limit
        meta_item = {
            'наименование': f"Поддон с '{self.base_item['наименование']}'", 'base_item_name': self.base_item['наименование'],
            'форма': 'pallet', 'вес': total_w, 'места': len(packed_items),
            'размеры_исходные': {'length': self.pallet_info['length'], 'width': self.pallet_info['width'], 'height': total_h},
            'components': {'pallet_info': self.pallet_info, 'packed_items': packed_items, 'layout': layout, 'layers': num_layers},
            'constraints': pallet_constraints, # Используем новые, исправленные ограничения
            'color': self.base_item['color']
        }
        self.palletized_items.append(meta_item)

    def _calculate_best_layer(self):
        """Рассчитывает оптимальное количество предметов на слое поддона."""
        p_l = Decimal(str(self.pallet_info['length']))
        p_w = Decimal(str(self.pallet_info['width']))
        if self.base_item['форма'] == 'box':
            l = Decimal(str(self.base_item['размеры_исходные']['length']))
            w = Decimal(str(self.base_item['размеры_исходные']['width']))
            if l == 0 or w == 0: return 0, {}
            num_l1 = (p_l / l).to_integral_value(rounding='ROUND_DOWN')
            num_w1 = (p_w / w).to_integral_value(rounding='ROUND_DOWN')
            n1 = num_l1 * num_w1
            num_l2 = (p_l / w).to_integral_value(rounding='ROUND_DOWN')
            num_w2 = (p_w / l).to_integral_value(rounding='ROUND_DOWN')
            n2 = num_l2 * num_w2
            if n1 >= n2: return int(n1), {'l_axis':'length', 'w_axis':'width'}
            else: return int(n2), {'l_axis':'width', 'w_axis':'length'}
        elif self.base_item['форма'] == 'cylinder':
            packing_mode = self.base_item.get('constraints', {}).get('pallet_packing_mode', 'automatic')
            d = Decimal(str(self.base_item['размеры_исходные']['diameter']))
            if d <= 0: return 0, {}
            count_grid = int((p_l / d).to_integral_value(rounding='ROUND_DOWN') * (p_w / d).to_integral_value(rounding='ROUND_DOWN'))
            count_staggered_A, count_staggered_B = 0, 0
            sqrt_3_div_2 = Decimal(3).sqrt() / 2
            if p_l >= d and p_w >= d:
                items_in_row_full = (p_l / d).to_integral_value(rounding='ROUND_DOWN')
                items_in_row_offset = ((p_l - d / 2) / d).to_integral_value(rounding='ROUND_DOWN')
                num_rows = 1 + ((p_w - d) / (d * sqrt_3_div_2)).to_integral_value(rounding='ROUND_DOWN')
                if num_rows > 0:
                     num_full_rows = (num_rows / 2).to_integral_value(rounding='ROUND_CEILING')
                     num_offset_rows = (num_rows / 2).to_integral_value(rounding='ROUND_DOWN')
                     count_staggered_A = int(num_full_rows * items_in_row_full + num_offset_rows * items_in_row_offset)
            if p_w >= d and p_l >= d:
                items_in_row_full = (p_w / d).to_integral_value(rounding='ROUND_DOWN')
                items_in_row_offset = ((p_w - d / 2) / d).to_integral_value(rounding='ROUND_DOWN')
                num_rows = 1 + ((p_l - d) / (d * sqrt_3_div_2)).to_integral_value(rounding='ROUND_DOWN')
                if num_rows > 0:
                    num_full_rows = (num_rows / 2).to_integral_value(rounding='ROUND_CEILING')
                    num_offset_rows = (num_rows / 2).to_integral_value(rounding='ROUND_DOWN')
                    count_staggered_B = int(num_full_rows * items_in_row_full + num_offset_rows * items_in_row_offset)
            
            if packing_mode == 'grid': return count_grid, {'l_axis':'diameter', 'w_axis':'diameter'}
            elif packing_mode == 'staggered': return max(count_staggered_A, count_staggered_B), {'l_axis':'diameter', 'w_axis':'diameter'}
            else: return max(count_grid, count_staggered_A, count_staggered_B), {'l_axis':'diameter', 'w_axis':'diameter'}
        return 0, {}

class TransportUnitPacker:
    """Класс для упаковки предметов в одну транспортную единицу."""
    def __init__(self, unit_info, packing_mode, calculation_model='2d', curb_weight_override=None):
        self.unit_name = unit_info['name']
        self.length = Decimal(str(unit_info['length']))
        self.width = Decimal(str(unit_info['width']))
        self.height = Decimal(str(unit_info['height']))
        self.max_total_vehicle_weight = Decimal(str(unit_info['max_weight']))
        self.placed_items = []
        self.total_cargo_weight = Decimal('0.0')
        self.packing_mode = packing_mode
        self.calculation_model = calculation_model
        self.is_vehicle = 'curb_axle_loads' in unit_info
        if self.is_vehicle:
            self.axle_calculator = AxleLoadCalculator(unit_info)
            if 'tractor_curb_weight' in unit_info and 'trailer_curb_weight' in unit_info:
                self.default_curb_weight = Decimal(str(unit_info['tractor_curb_weight'])) + Decimal(str(unit_info['trailer_curb_weight']))
            else:
                self.default_curb_weight = sum(Decimal(str(l)) for l in unit_info['curb_axle_loads'])
            self.effective_curb_weight = Decimal(str(curb_weight_override)) if curb_weight_override is not None else self.default_curb_weight
            self.payload_capacity = self.max_total_vehicle_weight - self.effective_curb_weight
        else:
            # Для контейнеров тоже создаем калькулятор для доступа к _calculate_3d_cg
            self.axle_calculator = AxleLoadCalculator(unit_info)
            self.payload_capacity = Decimal(str(unit_info['max_weight']))
            self.effective_curb_weight = Decimal('0.0')
            self.max_total_vehicle_weight = self.payload_capacity

    def get_orientations(self, item):
        """Возвращает список возможных ориентаций с учетом приоритета."""
        # Если ориентации заданы пользователем, используем только их
        if 'allowed_orientations' in item['constraints'] and item['constraints']['allowed_orientations']:
            return [(Decimal(str(d[0])), Decimal(str(d[1])), Decimal(str(d[2]))) for d in item['constraints']['allowed_orientations']]
        dims = item['размеры_исходные']
        ordered_orientations = []
        if item['форма'] == 'pallet':
            ordered_orientations.append((Decimal(str(dims['length'])), Decimal(str(dims['width'])), Decimal(str(dims['height']))))
        
        elif item['форма'] == 'box':
            l, w, h = Decimal(str(dims['length'])), Decimal(str(dims['width'])), Decimal(str(dims['height']))
            
            # Приоритет №1: Стабильная ориентация, как ввел пользователь
            stable_orientation = (l, w, h)
            ordered_orientations.append(stable_orientation)
            
            # Добавляем все остальные уникальные ориентации
            all_perms = set(permutations([l, w, h]))
            for perm in all_perms:
                if perm not in ordered_orientations:
                    ordered_orientations.append(perm)
        elif item['форма'] == 'cylinder':
            d, h = Decimal(str(dims['diameter'])), Decimal(str(dims['height']))
            
            vertical = (d, d, h)
            horizontal_1 = (h, d, d)
            horizontal_2 = (d, h, d)
            
            # Определяем ориентацию по умолчанию
            default_orientation = item.get('ориентация', 'vertical' if item.get('тип_груза') == 'Бочки' else 'horizontal')
            # Добавляем сначала приоритетную, затем остальные
            if default_orientation == 'vertical':
                ordered_orientations.extend([vertical, horizontal_1, horizontal_2])
            else: # horizontal
                ordered_orientations.extend([horizontal_1, horizontal_2, vertical])
        # Удаляем дубликаты, сохраняя порядок
        seen = set()
        orientations = [x for x in ordered_orientations if not (x in seen or seen.add(x))]
        return orientations

    def try_place_item(self, item):
        """Пытается разместить предмет в транспортной единице."""
        for dims_tuple in self.get_orientations(item):
            dims = list(dims_tuple)
            position = self.find_best_position(item, dims)
            if position:
                item['dims'] = [float(d) for d in dims]
                item['position'] = [float(p) for p in position]
                self.placed_items.append(item)
                self.total_cargo_weight += Decimal(str(item['вес']))
                return True
        return False

    def find_best_position(self, item, dims):
        """Находит наилучшее положение для размещения предмета."""
        potential_positions = []
        STEP_SIZE = Decimal('0.1')
        item_dim_x, item_dim_y, item_dim_z = dims
        for z_val in np.arange(0, float(self.height - item_dim_z) + float(STEP_SIZE), float(STEP_SIZE)):
            z = Decimal(str(z_val))
            for x_val in np.arange(0, float(self.length - item_dim_x) + float(STEP_SIZE), float(STEP_SIZE)):
                x = Decimal(str(x_val))
                for y_val in np.arange(0, float(self.width - item_dim_y) + float(STEP_SIZE), float(STEP_SIZE)):
                    y = Decimal(str(y_val))
                    potential_positions.append((x, y, z))
        
        for p_item in self.placed_items:
            px, py, pz = (Decimal(str(c)) for c in p_item['position'])
            dx, dy, dz = (Decimal(str(c)) for c in p_item['dims'])
            potential_positions.extend([(px + dx, py, pz), (px, py + dy, pz), (px, py, pz + dz),
                                        (px, Decimal('0'), pz), (Decimal('0'), py, pz), (Decimal('0'), Decimal('0'), pz)])
        potential_positions = sorted(list(set(potential_positions)), key=lambda p: (p[2], p[0], p[1]))
        
        best_overall_score = float('inf')
        best_pos_found = None
        for pos in potential_positions:
            if not self._check_basic_validity(item, pos, dims):
                continue
            current_score = 0.0
            if self.is_vehicle and self.packing_mode != 'density':
                hypothetical_item = item.copy()
                hypothetical_item['position'] = [float(p) for p in pos]
                hypothetical_item['dims'] = [float(d) for d in dims]
                temp_placed_items = self.placed_items + [hypothetical_item]
                
                axle_score = self.axle_calculator._evaluate_axle_load_score(
                    temp_placed_items,
                    self.effective_curb_weight,
                    self.max_total_vehicle_weight,
                    self.calculation_model
                )
                
                if axle_score >= 1_000_000_000:
                    continue
                current_score = axle_score
            if current_score < best_overall_score:
                best_overall_score = current_score
                best_pos_found = pos
                # В небезопасных режимах берем первую подходящую позицию
                if self.packing_mode == 'density':
                    break
        
        return best_pos_found

    def _check_basic_validity(self, item, pos, dims):
        """Проверяет, помещается ли предмет в единицу без перекрытий и превышения полезной нагрузки."""
        pos_x, pos_y, pos_z = pos
        dim_x, dim_y, dim_z = dims
        epsilon = Decimal('1e-9') 
        if (pos_x < -epsilon or pos_x + dim_x > self.length + epsilon or
            pos_y < -epsilon or pos_y + dim_y > self.width + epsilon or
            pos_z < -epsilon or pos_z + dim_z > self.height + epsilon):
            return False
        if self.total_cargo_weight + Decimal(str(item['вес'])) > self.payload_capacity + epsilon:
            return False
        for p_item in self.placed_items:
            px, py, pz = (Decimal(str(c)) for c in p_item['position'])
            dx, dy, dz = (Decimal(str(c)) for c in p_item['dims'])
            
            if ((pos_x < px + dx - epsilon) and (pos_x + dim_x > px + epsilon) and
                (pos_y < py + dy - epsilon) and (pos_y + dim_y > py + epsilon) and
                (pos_z < pz + dz - epsilon) and (pos_z + dim_z > pz + epsilon)):
                return False
        
        if pos_z > epsilon: 
            if not self.check_stacking_constraints(item, pos, dims):
                return False
        return True

    def check_stacking_constraints(self, new_item, pos, dims):
        """Проверяет ограничения штабелирования для нового предмета."""
        potential_supports = []
        epsilon = Decimal('1e-9')
        for p_item in self.placed_items:
            if abs(Decimal(str(p_item['position'][2])) + Decimal(str(p_item['dims'][2])) - pos[2]) < epsilon:
                ix_min = max(pos[0], Decimal(str(p_item['position'][0])))
                ix_max = min(pos[0] + dims[0], Decimal(str(p_item['position'][0] + p_item['dims'][0])))
                iy_min = max(pos[1], Decimal(str(p_item['position'][1])))
                iy_max = min(pos[1] + dims[1], Decimal(str(p_item['position'][1] + p_item['dims'][1])))
                
                if ix_max > ix_min + epsilon and iy_max > iy_min + epsilon:
                    potential_supports.append(p_item)
        
        if not potential_supports: return False
        
        for support_item in potential_supports:
            current_stack_bottom_item = support_item
            stack_above_bottom = []
            
            while True:
                found_lower_support = False
                for p_item_in_all_placed in self.placed_items:
                    if (abs(Decimal(str(p_item_in_all_placed['position'][2])) + Decimal(str(p_item_in_all_placed['dims'][2])) - Decimal(str(current_stack_bottom_item['position'][2]))) < epsilon and
                        max(Decimal(str(current_stack_bottom_item['position'][0])), Decimal(str(p_item_in_all_placed['position'][0]))) < min(Decimal(str(current_stack_bottom_item['position'][0] + current_stack_bottom_item['dims'][0])), Decimal(str(p_item_in_all_placed['position'][0] + p_item_in_all_placed['dims'][0]))) - epsilon and
                        max(Decimal(str(current_stack_bottom_item['position'][1])), Decimal(str(p_item_in_all_placed['position'][1]))) < min(Decimal(str(current_stack_bottom_item['position'][1] + current_stack_bottom_item['dims'][1])), Decimal(str(p_item_in_all_placed['position'][1] + p_item_in_all_placed['dims'][1]))) - epsilon):
                        
                        stack_above_bottom.insert(0, current_stack_bottom_item)
                        current_stack_bottom_item = p_item_in_all_placed
                        found_lower_support = True
                        break
                if not found_lower_support or Decimal(str(current_stack_bottom_item['position'][2])) < epsilon:
                    base_item = current_stack_bottom_item
                    break
            constraints = base_item.get('constraints', {})
            can_stack = True
            if 'max_stack_height' in constraints:
                stack_height = (pos[2] + dims[2]) - Decimal(str(base_item['position'][2]))
                if stack_height > Decimal(str(constraints['max_stack_height'])) + epsilon: can_stack = False
            if can_stack and 'max_stack_layers' in constraints:
                current_layers = len(stack_above_bottom) + 1
                if current_layers > constraints['max_stack_layers']: can_stack = False
            
            if can_stack and 'max_stack_load' in constraints:
                current_stack_load = sum(Decimal(str(item_in_stack['вес'])) for item_in_stack in stack_above_bottom)
                current_stack_load += Decimal(str(new_item['вес']))
                if current_stack_load > Decimal(str(constraints['max_stack_load'])) + epsilon: can_stack = False
            if can_stack: return True
        
        return False

class PackingManager:
    """Класс для управления процессом упаковки предметов в несколько транспортных единиц."""
    def __init__(self, packing_priority='volume', packing_mode='density', calculation_model='2d'):
        self.transport_units = []
        self.raw_items = []
        self.packing_priority = packing_priority
        self.packing_mode = packing_mode
        self.calculation_model = calculation_model

    def add_raw_item(self, item):
        """Добавляет исходный предмет (или несколько копий, если указано количество мест)."""
        self.raw_items.extend([item.copy() for _ in range(item['места'])])

    def _apply_packing_priority(self, items):
        """Применяет приоритет упаковки к списку предметов."""
        has_horizontal_cylinders = any(item['форма'] == 'cylinder' and item.get('ориентация') == 'horizontal' for item in items)
        has_boxes = any(item['форма'] in ['box', 'pallet'] for item in items)
        if has_horizontal_cylinders and has_boxes:
            options = {'1': 'Только другие рулоны (коробки будут уложены вниз)', '2': 'Без ограничений (стандартная укладка)'}
            choice = get_validated_choice("\n--- Уточнение по укладке смешанных грузов ---\nЧто разрешено грузить на горизонтальные рулоны?", options)
            if choice is None: return None
            if choice == '1':
                print("ИНФО: Установлен приоритет: коробки и паллеты укладываются в первую очередь.")
                base_group = [item for item in items if not (item['форма'] == 'cylinder' and item.get('ориентация') == 'horizontal')]
                top_group = [item for item in items if item['форма'] == 'cylinder' and item.get('ориентация') == 'horizontal']
                if self.packing_priority == 'volume':
                    base_group.sort(key=get_item_volume, reverse=True)
                    top_group.sort(key=get_item_volume, reverse=True)
                elif self.packing_priority == 'weight':
                    base_group.sort(key=itemgetter('вес'), reverse=True)
                    top_group.sort(key=itemgetter('вес'), reverse=True)
                return base_group + top_group
        if self.packing_priority == 'volume': items.sort(key=get_item_volume, reverse=True)
        elif self.packing_priority == 'weight': items.sort(key=itemgetter('вес'), reverse=True)
        return items

    def pack_items(self, available_unit_types, curb_weight_override):
        """
        Основной метод упаковки, который может обрабатывать как один тип ТС, так и несколько.
        """
        final_items = self._prepare_items_for_packing()
        remaining_items = self._apply_packing_priority(final_items)
        if remaining_items is None:
            print("Расчет прерван пользователем.")
            return []
        
        unpacked_items = []
        # Если режим НЕ 'density' или если доступен только один тип ТС, используем старую простую логику.
        if self.packing_mode != 'density' or len(available_unit_types) == 1:
            base_unit_info = available_unit_types[0]
            self.transport_units.append(TransportUnitPacker(base_unit_info, self.packing_mode, self.calculation_model, curb_weight_override))
            
            while remaining_items:
                item_to_place = remaining_items.pop(0)
                placed = False
                for unit_packer in self.transport_units:
                    if unit_packer.try_place_item(item_to_place.copy()):
                        placed = True
                        break
                if not placed:
                    new_packer = TransportUnitPacker(base_unit_info, self.packing_mode, self.calculation_model, curb_weight_override)
                    if new_packer.try_place_item(item_to_place.copy()):
                        self.transport_units.append(new_packer)
                    else:
                        unpacked_items.append(item_to_place)
        else:
            # Иначе (режим 'density' И несколько типов ТС), используем новый алгоритм оптимизации.
            while remaining_items:
                best_placement = {'packer_index': -1, 'final_packer_state': None, 'packed_item_indices': [], 'packed_count': 0}
                # 1. Проверяем, сколько еще предметов можно добавить в уже существующие ТС
                for i, tu in enumerate(self.transport_units):
                    packer_copy = copy.deepcopy(tu)
                    packed_indices_this_try = []
                    for item_idx, item in enumerate(remaining_items):
                        if packer_copy.try_place_item(item.copy()):
                            packed_indices_this_try.append(item_idx)
                    
                    if len(packed_indices_this_try) > best_placement['packed_count']:
                        best_placement.update({'packed_count': len(packed_indices_this_try), 'packed_item_indices': packed_indices_this_try, 'final_packer_state': packer_copy, 'packer_index': i})
                # 2. Проверяем, сколько предметов можно упаковать в новый контейнер каждого доступного типа
                for unit_info in available_unit_types:
                    packer_copy = TransportUnitPacker(unit_info, self.packing_mode, self.calculation_model, curb_weight_override)
                    packed_indices_this_try = []
                    for item_idx, item in enumerate(remaining_items):
                        if packer_copy.try_place_item(item.copy()):
                            packed_indices_this_try.append(item_idx)
                    if len(packed_indices_this_try) > best_placement['packed_count']:
                        best_placement.update({'packed_count': len(packed_indices_this_try), 'packed_item_indices': packed_indices_this_try, 'final_packer_state': packer_copy, 'packer_index': -1})
                # 3. Применяем лучшее найденное решение
                if best_placement['packed_count'] > 0:
                    if best_placement['packer_index'] != -1:
                        self.transport_units[best_placement['packer_index']] = best_placement['final_packer_state']
                    else:
                        self.transport_units.append(best_placement['final_packer_state'])
                    
                    indices_to_remove = set(best_placement['packed_item_indices'])
                    remaining_items = [item for i, item in enumerate(remaining_items) if i not in indices_to_remove]
                else:
                    unpacked_items = remaining_items
                    break # Если ничего не удалось разместить, выходим из цикла
        # Выполняем поперечное центрирование для всех ТС после укладки
        for unit_packer_obj in self.transport_units:
            if unit_packer_obj.is_vehicle:
                self._adjust_transverse_balance(unit_packer_obj)
        return unpacked_items

    def _adjust_transverse_balance(self, unit_packer_obj):
        """Автоматически центрирует весь груз по ширине кузова."""
        if not unit_packer_obj.placed_items or not unit_packer_obj.is_vehicle:
            return
        # Для расчета ЦТ нужен AxleLoadCalculator, который есть только у ТС
        if not hasattr(unit_packer_obj, 'axle_calculator'):
            return
        current_cg_cargo = unit_packer_obj.axle_calculator._calculate_3d_cg(unit_packer_obj.placed_items)
        current_cgy = Decimal(str(current_cg_cargo['y']))
        
        target_cgy = unit_packer_obj.width / 2
        shift_y = target_cgy - current_cgy
        
        if abs(shift_y) < Decimal('0.01'): # Не сдвигаем, если груз уже отцентрован
            return
        min_y = min(Decimal(str(item['position'][1])) for item in unit_packer_obj.placed_items)
        max_y = max(Decimal(str(item['position'][1])) + Decimal(str(item['dims'][1])) for item in unit_packer_obj.placed_items)
        # Проверяем, что после сдвига груз не выйдет за пределы кузова
        if min_y + shift_y >= Decimal('-1e-9') and max_y + shift_y <= unit_packer_obj.width + Decimal('1e-9'):
            for item in unit_packer_obj.placed_items:
                item['position'][1] = float(Decimal(str(item['position'][1])) + shift_y)
            print(f"ИНФО: Груз в '{unit_packer_obj.unit_name}' был автоматически сцентрирован по ширине (сдвиг: {float(shift_y):.3f} м).")
        else:
            print(f"ПРЕДУПРЕЖДЕНИЕ: Не удалось полностью сцентрировать груз в '{unit_packer_obj.unit_name}' без выхода за габариты.")

    def _prepare_items_for_packing(self):
        """Подготавливает предметы к упаковке, группируя их на поддонах при необходимости."""
        pallet_groups, floor_items = {}, []
        for item in self.raw_items:
            if 'constraints' not in item: item['constraints'] = {}
            if item.get('on_pallet', False):
                pallet_key = item['constraints']['pallet_info']['name']
                if pallet_key not in pallet_groups: pallet_groups[pallet_key] = []
                pallet_groups[pallet_key].append(item)
            else: floor_items.append(item)
        final_list = floor_items
        for key, items in pallet_groups.items():
            grouped_items = {}
            for item in items:
                item_id = (item['наименование'], item['форма'], frozenset(item['размеры_исходные'].items()))
                if item_id not in grouped_items: grouped_items[item_id] = []
                grouped_items[item_id].append(item)
            for item_group in grouped_items.values():
                palletizer = PalletizedGroup(item_group, item_group[0]['constraints']['pallet_info'])
                final_list.extend(palletizer.palletized_items)
        return final_list

# --- ФУНКЦИИ ВВОДА И ВИЗУАЛИЗАЦИИ ---

def input_cargo(available_units, pallet_db):
    """Запрашивает у пользователя информацию о грузе."""
    cargo_items = []
    cargo_types = {'1': "Коробки", '2': "Мешки", '3': "Биг бэги", '4': "Бочки", '5': "Рулоны"}
    shapes = {'1':'box', '2':'box', '3':'box', '4':'cylinder', '5':'cylinder'}
    while True:
        name_prompt = "\nНаименование груза ('1' для завершения, 'q' для выхода в начало): "
        name = input(name_prompt).strip()
        if name == '1': break
        if name.lower() == 'q': return None
        type_choice = get_validated_choice("Выберите тип груза:", cargo_types)
        if type_choice is None: continue
        type_name, shape = cargo_types[type_choice], shapes[type_choice]
        item = {'наименование': name, 'тип_груза': type_name, 'форма': shape, 'constraints': {}, 'on_pallet': False}
        while True:
            if shape == 'box':
                l = get_validated_float("Длина (м): ");
                if l is None: break
                w = get_validated_float("Ширина (м): ");
                if w is None: break
                h = get_validated_float("Высота (м): ");
                if h is None: break
                item['размеры_исходные'] = {'length': l, 'width': w, 'height': h}
            elif shape == 'cylinder':
                prompt = "Высота" if type_name=="Бочки" else "Длина"
                d = get_validated_float("Диаметр (м): ");
                if d is None: break
                h = get_validated_float(f"{prompt} (м): ");
                if h is None: break
                item['размеры_исходные'] = {'diameter': d, 'height': h}
                # Устанавливаем ориентацию по умолчанию
                item['ориентация'] = 'vertical' if type_name=="Бочки" else 'horizontal'
            weight = get_validated_float("Вес (кг): ");
            if weight is None: break
            item['вес'] = weight
            if not pre_check_cargo(item, available_units):
                if get_validated_choice("Желаете изменить параметры этого груза?", {'1':'Да', '2':'Нет'}) == '1': continue
                else: break
            
            if item.get('on_pallet'):
                if not check_pallet_fit(item, item['constraints']['pallet_info']):
                    options = { '1': 'Изменить габариты/вес груза', '2': 'Выбрать другой поддон', '3': 'Разместить груз без поддона' }
                    action = get_validated_choice("Выберите действие:", options)
                    if action == '1': continue
                    if action == '2': item['on_pallet'] = False
                    if action == '3': item['on_pallet'] = False; break
                    if action is None: break
                else: break
            else: break
        if item.get('размеры_исходные') is None or item.get('вес') is None: continue
        count = get_validated_int("Количество мест: ");
        if count is None: continue
        item['места'] = count
        item['color'] = f'hsl({np.random.randint(0,360)},70%,50%)'
        if type_name != "Биг бэги" and not item.get('on_pallet'):
            pallet_choice = get_validated_choice("Разместить этот груз на поддоне?", {'1': 'Да', '2': 'Нет'})
            if pallet_choice is None: continue
            if pallet_choice == '1':
                while True:
                    pallet_options = {str(i+1): v['name'] for i, v in enumerate(pallet_db.values())}
                    pallet_key_choice = get_validated_choice("Выберите тип поддона:", pallet_options)
                    if pallet_key_choice is None: break
                    selected_key = list(pallet_db.keys())[int(pallet_key_choice) - 1]
                    pallet_info = pallet_db[selected_key]
                    if check_pallet_fit(item, pallet_info):
                        item['on_pallet'] = True
                        item['constraints']['pallet_info'] = pallet_info
                        if shape == 'cylinder':
                            packing_options = {'1': 'Прямоугольная', '2': 'Шахматная', '3': 'Оптимальная (автоматическая)'}
                            packing_choice = get_validated_choice("\nВыберите тип укладки на поддоне:", packing_options)
                            if packing_choice is None: continue
                            if packing_choice == '1': item['constraints']['pallet_packing_mode'] = 'grid'
                            elif packing_choice == '2': item['constraints']['pallet_packing_mode'] = 'staggered'
                            else: item['constraints']['pallet_packing_mode'] = 'automatic'
                        break
                    else:
                        if get_validated_choice("Этот поддон не подходит. Попробовать другой?", {'1':'Да', '2':'Нет'}) != '1': break
        if input_advanced_constraints(item) is None: continue
        cargo_items.append(item)
    return cargo_items

def input_advanced_constraints(item):
    """Запрашивает у пользователя расширенные ограничения для груза."""
    print(f"\n--- Расширенные настройки для груза '{item['наименование']}' ---")
    if item.get('on_pallet'):
        tier_choice = get_validated_choice("Разрешить использование поддонов на вторых и последующих ярусах?", 
                                           {'1': 'Да', '2': 'Нет (стандартный вариант, груз будет ставиться без поддона)'})
        if tier_choice is None: return None
        item['constraints']['pallets_on_all_tiers'] = (tier_choice == '1')
    orient_choice = get_validated_choice("Изменить разрешенные наклоны груза?", {'1':'Нет', '2':'Да'})
    if orient_choice is None: return None
    if orient_choice == '2':
        dims_исх = item['размеры_исходные']
        if item['форма'] == 'box':
            l, w, h = dims_исх.values()
            all_orients = list(set(permutations([l, w, h])))
            choice = get_validated_choice("Запретить наклон, при котором вертикальной осью становится:", {'1':'Ширина', '2':'Высота', '3':'И Ширина, и Высота'})
            if choice is None: return None
            if choice == '1': item['constraints']['allowed_orientations'] = [o for o in all_orients if o[2] != w]
            elif choice == '2': item['constraints']['allowed_orientations'] = [o for o in all_orients if o[2] != h]
            elif choice == '3': item['constraints']['allowed_orientations'] = [o for o in all_orients if o[2] != w and o[2] != h]
        elif item['форма'] == 'cylinder':
            orient_options = {'1': 'Только вертикально', '2': 'Только горизонтально'}
            cyl_orient_choice = get_validated_choice("Разрешенная ориентация:", orient_options)
            if cyl_orient_choice is None: return None
            d,h = dims_исх['diameter'], dims_исх['height']
            if cyl_orient_choice == '1':
                item['constraints']['allowed_orientations'] = [(d, d, h)]; item['ориентация'] = 'vertical'
            elif cyl_orient_choice == '2':
                item['constraints']['allowed_orientations'] = [(h, d, d), (d, h, d)]; item['ориентация'] = 'horizontal'
    stack_choice = get_validated_choice("Изменить настройки штабелирования?", {'1':'Нет', '2':'Да'})
    if stack_choice is None: return None
    if stack_choice == '2':
        choices = input("Выберите ограничение (можно вводить несколько, например '13'):\n 1 - Допустимая ВЫСОТА штабеля\n 2 - Допустимое КОЛИЧЕСТВО МЕСТ в штабеле\n 3 - Допустимая НАГРУЗКА на нижнее место\nВаш выбор ('q' для выхода): ")
        if 'q' in choices.lower(): return None
        if '1' in choices:
            height_limit = get_validated_float("  Введите макс. высоту штабеля (м): ")
            if height_limit is None: return None
            item['constraints']['max_stack_height'] = height_limit
        if '2' in choices:
            layers_limit = get_validated_int("  Введите макс. количество слоев (шт): ")
            if layers_limit is None: return None
            item['constraints']['max_stack_layers'] = layers_limit
        if '3' in choices:
            load_limit = get_validated_float("  Введите макс. нагрузку на нижнее место (кг): ")
            if load_limit is None: return None
            item['constraints']['max_stack_load'] = load_limit
    return item

def get_axle_positions_from_user(unit_info):
    """Запрашивает у пользователя уточнение положения осей транспортного средства."""
    if 'axle_positions' not in unit_info: return unit_info
    print("\n--- Уточнение положения осей ---")
    current_positions_str = ", ".join(map(str, unit_info['axle_positions']))
    prompt = f"Текущие положения осей от переднего края: [{current_positions_str}] м.\nХотите уточнить их?"
    choice = get_validated_choice(prompt, {'1': 'Да', '2': 'Нет, использовать текущие'})
    if choice is None or choice == '2': return unit_info
    config_choice = get_validated_choice("Выберите способ задания положений:", {'1': 'Ввести значения вручную'})
    if config_choice is None: return unit_info
    if config_choice == '1':
        new_positions = []
        num_axles = unit_info.get('axles', len(unit_info['axle_positions']))
        print(f"Введите {num_axles} значений положений осей последовательно.")
        for i in range(num_axles):
            pos = get_validated_float(f"Положение оси {i+1} от переднего края транспортного средства (м): ")
            if pos is None:
                print("Ввод отменен. Используются исходные значения.")
                return unit_info
            new_positions.append(pos)
        
        unit_info['axle_positions'] = new_positions
        print(f"Новые положения осей установлены: {new_positions}")
    return unit_info

def get_3d_parameters_from_user(unit_info):
    """Запрашивает у пользователя уточнение 3D параметров ТС."""
    print("\n--- Уточнение параметров для 3D-расчета осевых нагрузок ---")
    
    # Высота ЦТ пустого ТС
    default_cg_h = unit_info.get('cg_height_empty', 1.5)
    prompt = f"Текущая высота ЦТ пустого ТС: {default_cg_h:.2f} м.\nХотите уточнить?"
    choice = get_validated_choice(prompt, {'1': 'Да', '2': 'Нет, использовать текущее'})
    if choice == '1':
        new_val = get_validated_float("  Введите новую высоту ЦТ (м): ")
        if new_val is not None: unit_info['cg_height_empty'] = new_val
    
    # Ширина передней колеи
    default_tw_f = unit_info.get('track_width_front', 2.0)
    prompt = f"Текущая ширина передней колеи: {default_tw_f:.2f} м.\nХотите уточнить?"
    choice = get_validated_choice(prompt, {'1': 'Да', '2': 'Нет, использовать текущее'})
    if choice == '1':
        new_val = get_validated_float("  Введите новую ширину передней колеи (м): ")
        if new_val is not None: unit_info['track_width_front'] = new_val
        
    # Ширина задней колеи
    default_tw_r = unit_info.get('track_width_rear', 2.0)
    prompt = f"Текущая ширина задней колеи: {default_tw_r:.2f} м.\nХотите уточнить?"
    choice = get_validated_choice(prompt, {'1': 'Да', '2': 'Нет, использовать текущее'})
    if choice == '1':
        new_val = get_validated_float("  Введите новую ширину задней колеи (м): ")
        if new_val is not None: unit_info['track_width_rear'] = new_val
    # Параметры седла (только для автопоездов)
    if 'saddle_position_x' in unit_info:
        default_sp_x = unit_info.get('saddle_position_x', 7.0)
        prompt = f"Текущая X-позиция седла от переднего края тягача: {default_sp_x:.2f} м.\nХотите уточнить?"
        choice = get_validated_choice(prompt, {'1': 'Да', '2': 'Нет, использовать текущее'})
        if choice == '1':
            new_val = get_validated_float("  Введите новую X-позицию седла (м): ")
            if new_val is not None: unit_info['saddle_position_x'] = new_val
        default_s_h = unit_info.get('saddle_height', 1.3)
        prompt = f"Текущая высота седла от дороги: {default_s_h:.2f} м.\nХотите уточнить?"
        choice = get_validated_choice(prompt, {'1': 'Да', '2': 'Нет, использовать текущее'})
        if choice == '1':
            new_val = get_validated_float("  Введите новую высоту седла (м): ")
            if new_val is not None: unit_info['saddle_height'] = new_val
            
    return unit_info

def visualize_packed_units(manager, unpacked_items):
    """Визуализирует упакованные транспортные единицы и неразмещенные предметы."""
    if not manager.transport_units and not unpacked_items: return
    fig = go.Figure()
    x_offset = 0
    for unit_packer_obj in manager.transport_units:
        if not unit_packer_obj.placed_items: continue
        original_unit_info = unit_packer_obj.axle_calculator.params if unit_packer_obj.is_vehicle else None
        
        unit_total_length = float(unit_packer_obj.length)
        if original_unit_info and 'axle_positions' in original_unit_info:
            unit_total_length = float(max(original_unit_info['axle_positions']))
        
        add_transport_unit_visualization(fig, x_offset, 0, 0, original_unit_info, unit_packer_obj, manager.calculation_model)
        
        cargo_space_origin_x = x_offset
        if original_unit_info and 'saddle_position_x' in original_unit_info:
             kingpin_setback = float(original_unit_info.get('kingpin_setback', 1.0))
             saddle_x = float(original_unit_info.get('saddle_position_x', 3.6))
             cargo_space_origin_x += saddle_x - kingpin_setback
        for item in unit_packer_obj.placed_items: 
            add_cargo(fig, item, cargo_space_origin_x, (cargo_space_origin_x, 0, 0))
            
        x_offset += unit_total_length + 5.0
    if unpacked_items:
        max_l = max((item['размеры_исходные'].get('length', item['размеры_исходные'].get('diameter', 1)) for item in unpacked_items), default=10)
        max_w = max((item['размеры_исходные'].get('width', item['размеры_исходные'].get('diameter', 1)) for item in unpacked_items), default=10)
        
        floor_x = [x_offset, x_offset + max_l, x_offset + max_l, x_offset]
        floor_y = [0, 0, max_w, max_w]
        floor_z = [0, 0, 0, 0]
        fig.add_trace(go.Mesh3d(x=floor_x, y=floor_y, z=floor_z, color='lightgrey', opacity=0.5, name="Неразмещенный груз"))
        current_x, current_y, max_h_in_row = 0.0, 0.0, 0.0
        for item in unpacked_items:
            dims = item['размеры_исходные']
            item_l = dims.get('length', dims.get('diameter', 1))
            item_w = dims.get('width', dims.get('diameter', 1))
            item_h = dims.get('height', 1)
            if current_x + item_l > max_l:
                current_x = 0
                current_y += max_h_in_row
                max_h_in_row = 0
            
            item_vis = item.copy()
            if 'dims' not in item_vis:
                item_vis['dims'] = [item_l, item_w, item_h]
            item_vis['position'] = [current_x, current_y, 0]
            add_cargo(fig, item_vis, x_offset, (x_offset, 0, 0), opacity=0.5)
            current_x += item_l + 0.1
            max_h_in_row = max(max_h_in_row, item_w)
    fig.update_layout(
        title='Результаты упаковки',
        scene=dict(
            aspectmode='data', 
            camera=dict(eye=dict(x=1.5, y=-1.5, z=1.2)),
            xaxis=dict(title='Длина (м)', visible=True, showbackground=False, showspikes=False),
            yaxis=dict(title='Ширина (м)', visible=True, showbackground=False, showspikes=False),
            zaxis=dict(title='Высота (м)', visible=True, showbackground=False, showspikes=False)
        ),
        margin=dict(l=10, r=10, b=10, t=40), 
        showlegend=True
    )
    fig.show()

def _add_box_outline(fig, pos, dims, color='lightgray', width=4, name=None, showlegend=False):
    """Вспомогательная функция для отрисовки контура прямоугольника."""
    x, y, z = pos
    dx, dy, dz = dims
    verts = np.array([
        [x, y, z], [x + dx, y, z], [x + dx, y + dy, z], [x, y + dy, z],
        [x, y, z + dz], [x + dx, y, z + dz], [x + dx, y + dy, z + dz], [x, y + dy, z + dz]
    ])
    edges = [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]]
    edge_x, edge_y, edge_z = [], [], []
    for e in edges:
        edge_x.extend([verts[e[0]][0], verts[e[1]][0], None])
        edge_y.extend([verts[e[0]][1], verts[e[1]][1], None])
        edge_z.extend([verts[e[0]][2], verts[e[1]][2], None])
    fig.add_trace(go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z, mode='lines', 
        line=dict(color=color, width=width), 
        name=name, showlegend=showlegend, hoverinfo='name' if name else 'none'
    ))

def add_transport_unit_visualization(fig, x_offset, y_offset, z_offset, original_unit_info, unit_packer_obj, calculation_model):
    """Добавляет визуализацию транспортной единицы, включая оси и метки."""
    is_articulated = unit_packer_obj.is_vehicle and original_unit_info and 'saddle_position_x' in original_unit_info
    # --- 1. Отрисовка кузова/кабины ---
    if is_articulated:
        # Рисуем детализированный автопоезд
        # Кабина тягача (условные размеры) - теперь только контур
        cab_length = float(original_unit_info.get('wheelbase', 3.8))
        cab_height = 3.0  # Условная высота кабины
        cab_width = float(unit_packer_obj.width) * 0.95 # Чуть уже кузова
        cab_y_pos = y_offset + (float(unit_packer_obj.width) - cab_width) / 2 # Центрируем
        _add_box_outline(fig, 
                         (x_offset, cab_y_pos, z_offset), 
                         (cab_length, cab_width, cab_height),
                         color='hsl(0,0%,50%)', 
                         name='Тягач (контур)', 
                         showlegend=False)
        # Грузовое пространство полуприцепа
        kingpin_setback = float(original_unit_info.get('kingpin_setback', 1.0))
        saddle_x = float(original_unit_info.get('saddle_position_x', 3.6))
        trailer_start_x = x_offset + saddle_x - kingpin_setback
        trailer_dims = (float(unit_packer_obj.length), float(unit_packer_obj.width), float(unit_packer_obj.height))
        _add_box_outline(fig, 
                         (trailer_start_x, y_offset, z_offset), 
                         trailer_dims, 
                         name=unit_packer_obj.unit_name, 
                         showlegend=True)
    else:
        # Рисуем простой контейнер или одиночный грузовик
        unit_dims = (float(unit_packer_obj.length), float(unit_packer_obj.width), float(unit_packer_obj.height))
        _add_box_outline(fig, 
                         (x_offset, y_offset, z_offset), 
                         unit_dims, 
                         name=unit_packer_obj.unit_name, 
                         showlegend=True)
    # --- 2. Отрисовка осей и нагрузок (общая логика) ---
    if unit_packer_obj.is_vehicle and original_unit_info:
        axle_positions = original_unit_info.get('axle_positions', [])
        track_width_front = float(original_unit_info.get('track_width_front', 2.0))
        track_width_rear = float(original_unit_info.get('track_width_rear', 2.0))
        axle_line_z = z_offset - 0.2
        compliance_result = unit_packer_obj.axle_calculator.check_axle_load_compliance(unit_packer_obj.placed_items, unit_packer_obj.effective_curb_weight, unit_packer_obj.max_total_vehicle_weight, calculation_model)
        loads_info = unit_packer_obj.axle_calculator.get_loads(unit_packer_obj.placed_items, unit_packer_obj.effective_curb_weight, mode=calculation_model)
        calculated_loads = loads_info.get('total_axle_loads', [])
        wheel_loads = loads_info.get('wheel_loads', {})
        for idx, axle_pos_relative in enumerate(axle_positions):
            # Позиция оси всегда абсолютная от x_offset (бампера тягача)
            axle_x = x_offset + float(axle_pos_relative)
            track_width = track_width_front if idx == 0 else track_width_rear
            axle_y_start = y_offset + (float(unit_packer_obj.width) / 2) - (track_width / 2)
            axle_y_end = y_offset + (float(unit_packer_obj.width) / 2) + (track_width / 2)
            axle_color = 'red' if compliance_result['details']['individual_axle_exceeded'].get(idx, False) else 'green'
            fig.add_trace(go.Scatter3d(x=[axle_x, axle_x], y=[axle_y_start, axle_y_end], z=[axle_line_z, axle_line_z], mode='lines', line=dict(color=axle_color, width=8), name=f"Ось {idx+1}", showlegend=False, hoverinfo='none'))
            if '3d' in calculation_model and f'P{idx+1}_left' in wheel_loads:
                load_left = wheel_loads[f'P{idx+1}_left']
                load_right = wheel_loads[f'P{idx+1}_right']
                fig.add_trace(go.Scatter3d(x=[axle_x, axle_x], y=[axle_y_start, axle_y_end], z=[axle_line_z - 0.7, axle_line_z - 0.7], mode='text', text=[f"{load_left:.1f} кг", f"{load_right:.1f} кг"], textfont=dict(color="grey", size=12), showlegend=False, hoverinfo='none'))
            elif idx < len(calculated_loads):
                load_value = calculated_loads[idx]
                fig.add_trace(go.Scatter3d(x=[axle_x], y=[y_offset + float(unit_packer_obj.width) / 2], z=[axle_line_z - 0.7], mode='text', text=[f"Ось {idx+1}: {load_value:.1f} кг"], textfont=dict(color="grey", size=12), showlegend=False, hoverinfo='none'))
        # Метки передней и задней части грузового отсека
        cargo_space_start_x = x_offset if not is_articulated else x_offset + float(original_unit_info.get('saddle_position_x', 3.6)) - float(original_unit_info.get('kingpin_setback', 1.0))
        cargo_space_end_x = cargo_space_start_x + float(unit_packer_obj.length)
        
        fig.add_trace(go.Scatter3d(x=[cargo_space_start_x + 0.5], y=[y_offset + float(unit_packer_obj.width) / 2], z=[z_offset + float(unit_packer_obj.height) / 2], mode='text', text=["FP"], textfont=dict(color="black", size=16), showlegend=False, hoverinfo='none'))
        fig.add_trace(go.Scatter3d(x=[cargo_space_end_x - 0.5], y=[y_offset + float(unit_packer_obj.width) / 2], z=[z_offset + float(unit_packer_obj.height) / 2], mode='text', text=["BP"], textfont=dict(color="black", size=16), showlegend=False, hoverinfo='none'))

def add_cargo(fig, item, x_offset=0, cargo_space_origin=(0,0,0), opacity=1.0):
    """Добавляет визуализацию груза на график."""
    item_vis = item.copy()
    item_vis['position'] = (item['position'][0] + x_offset, item['position'][1], item['position'][2])
    
    # Передаем начало координат грузового пространства для расчета относительных координат в подсказке
    if item['форма'] == 'pallet': 
        add_pallet_cargo(fig, item_vis, cargo_space_origin, opacity)
    elif item['форма'] == 'box': 
        add_box_cargo(fig, item_vis, cargo_space_origin, with_edges=True, opacity=opacity)
    elif item['форма'] == 'cylinder': 
        add_cylinder_cargo(fig, item_vis, cargo_space_origin, opacity)

def add_pallet_cargo(fig, item, cargo_space_origin, opacity=1.0):
    """Добавляет визуализацию паллетизированного груза."""
    pallet_info = item['components']['pallet_info']
    packed_items = item['components']['packed_items']
    layers = item['components']['layers']
    px, py, pz = Decimal(str(item['position'][0])), Decimal(str(item['position'][1])), Decimal(str(item['position'][2]))
    pl, pw, ph = Decimal(str(item['dims'][0])), Decimal(str(item['dims'][1])), Decimal(str(item['dims'][2]))
    
    add_box_cargo(fig, {'position':(float(px),float(py),float(pz)), 'dims':(float(pl),float(pw),float(pallet_info['depth'])), 'color':'hsl(0,0%,30%)', 'наименование':item['наименование'] + " (поддон)"}, cargo_space_origin, with_edges=True, opacity=opacity)
    
    if not packed_items: return
    base_item = packed_items[0]
    base_item_height = Decimal(str(base_item['размеры_исходные']['height']))
    packing_style = base_item['constraints'].get('pallet_packing_mode', 'automatic')
    
    def generate_layer_positions(item_shape, pallet_dims, item_orig_dims, packing_style):
        """Генерирует позиции для предметов на одном слое поддона."""
        p_l, p_w = Decimal(str(pallet_dims['length'])), Decimal(str(pallet_dims['width']))
        positions = []
        if item_shape == 'box':
            item_l, item_w = Decimal(str(item_orig_dims['length'])), Decimal(str(item_orig_dims['width']))
            for i in range(int((p_l / item_l).to_integral_value(rounding='ROUND_DOWN'))):
                for j in range(int((p_w / item_w).to_integral_value(rounding='ROUND_DOWN'))):
                    positions.append((Decimal(i) * item_l, Decimal(j) * item_w))
            temp_positions_rotated = []
            for i in range(int((p_l / item_w).to_integral_value(rounding='ROUND_DOWN'))):
                for j in range(int((p_w / item_l).to_integral_value(rounding='ROUND_DOWN'))):
                    temp_positions_rotated.append((Decimal(i) * item_w, Decimal(j) * item_l))
            if len(temp_positions_rotated) > len(positions): positions = temp_positions_rotated
        elif item_shape == 'cylinder':
            d = Decimal(str(item_orig_dims['diameter']))
            sqrt3_half = Decimal(3).sqrt() / Decimal(2)
            count_grid = int((p_l / d).to_integral_value(rounding='ROUND_DOWN') * (p_w / d).to_integral_value(rounding='ROUND_DOWN'))
            count_staggered_A = 0
            if p_w >= d:
                n_l_full = (p_l / d).to_integral_value(rounding='ROUND_DOWN')
                n_l_offset = ((p_l - d / 2) / d).to_integral_value(rounding='ROUND_DOWN')
                num_rows = 1 + ((p_w - d) / (d * sqrt3_half)).to_integral_value(rounding='ROUND_DOWN')
                if num_rows > 0:
                     num_full_rows = (num_rows / 2).to_integral_value(rounding='ROUND_CEILING')
                     num_offset_rows = (num_rows / 2).to_integral_value(rounding='ROUND_DOWN')
                     count_staggered_A = int(num_full_rows * n_l_full + num_offset_rows * n_l_offset)
            count_staggered_B = 0
            if p_l >= d:
                n_w_full = (p_w / d).to_integral_value(rounding='ROUND_DOWN')
                n_w_offset = ((p_w - d / 2) / d).to_integral_value(rounding='ROUND_DOWN')
                num_rows = 1 + ((p_l - d) / (d * sqrt3_half)).to_integral_value(rounding='ROUND_DOWN')
                if num_rows > 0:
                    num_full_rows = (num_rows / 2).to_integral_value(rounding='ROUND_CEILING')
                    num_offset_rows = (num_rows / 2).to_integral_value(rounding='ROUND_DOWN')
                    count_staggered_B = int(num_full_rows * n_w_full + num_offset_rows * n_w_offset)
            count_staggered = max(count_staggered_A, count_staggered_B)
            if packing_style == 'grid' or (packing_style == 'automatic' and count_grid >= count_staggered):
                for i in range(int((p_l / d).to_integral_value(rounding='ROUND_DOWN'))):
                    for j in range(int((p_w / d).to_integral_value(rounding='ROUND_DOWN'))):
                        positions.append((Decimal(i) * d, Decimal(j) * d))
            elif packing_style == 'staggered' or (packing_style == 'automatic' and count_staggered > count_grid):
                best_staggered_positions = []
                if count_staggered_A >= count_staggered_B: # Укладка вдоль ширины
                    num_rows_w = 1 + ((p_w - d) / (d * sqrt3_half)).to_integral_value(rounding='ROUND_DOWN')
                    for row_idx in range(int(num_rows_w)):
                        offset_x = d / 2 if row_idx % 2 != 0 else Decimal('0')
                        current_row_len = p_l - offset_x
                        num_items_in_row = (current_row_len / d).to_integral_value(rounding='ROUND_DOWN')
                        for col_idx in range(int(num_items_in_row)):
                            best_staggered_positions.append((offset_x + Decimal(col_idx) * d, Decimal(row_idx) * d * sqrt3_half))
                else: # Укладка вдоль длины
                    num_rows_l = 1 + ((p_l - d) / (d * sqrt3_half)).to_integral_value(rounding='ROUND_DOWN')
                    for row_idx in range(int(num_rows_l)):
                        offset_y = d / 2 if row_idx % 2 != 0 else Decimal('0')
                        current_row_len = p_w - offset_y
                        num_items_in_row = (current_row_len / d).to_integral_value(rounding='ROUND_DOWN')
                        for col_idx in range(int(num_items_in_row)):
                            best_staggered_positions.append((Decimal(row_idx) * d * sqrt3_half, offset_y + Decimal(col_idx) * d))
                positions = best_staggered_positions
        return positions

    layer_positions = generate_layer_positions(base_item['форма'], pallet_info, base_item['размеры_исходные'], packing_style)
    current_item_index_in_packed_items = 0
    current_layer_z = pz + Decimal(str(pallet_info['depth']))
    for l_idx in range(layers):
        for pos_x, pos_y in layer_positions:
            if current_item_index_in_packed_items >= len(packed_items): break
            item_to_visualize = packed_items[current_item_index_in_packed_items]
            if item_to_visualize['форма'] == 'cylinder':
                diameter, height_cyl = item_to_visualize['размеры_исходные']['diameter'], item_to_visualize['размеры_исходные']['height']
                cargo_to_draw = item_to_visualize.copy()
                cargo_to_draw.update({'ориентация': 'vertical', 'position':(float(px + pos_x), float(py + pos_y), float(current_layer_z)), 'dims': (diameter, diameter, height_cyl)})
                add_cylinder_cargo(fig, cargo_to_draw, cargo_space_origin, opacity)
            elif item_to_visualize['форма'] == 'box':
                cargo_to_draw = item_to_visualize.copy()
                cargo_to_draw.update({'position':(float(px + pos_x), float(py + pos_y), float(current_layer_z)), 'dims': (item_to_visualize['размеры_исходные']['length'], item_to_visualize['размеры_исходные']['width'], item_to_visualize['размеры_исходные']['height'])})
                add_box_cargo(fig, cargo_to_draw, cargo_space_origin, opacity=opacity)
            current_item_index_in_packed_items += 1
        current_layer_z += base_item_height
        if current_item_index_in_packed_items >= len(packed_items): break

def add_box_cargo(fig, item, cargo_space_origin, with_edges=True, opacity=1.0):
    """Добавляет визуализацию прямоугольного груза."""
    x,y,z=item['position']; dx,dy,dz=item['dims']; shades=get_color_shades(item['color'])
    
    # Расчет относительных координат центра
    rel_x = (x - cargo_space_origin[0]) + dx / 2
    rel_y = (y - cargo_space_origin[1]) + dy / 2
    rel_z = (z - cargo_space_origin[2]) + dz / 2
    hover_text = f"<b>{item['наименование']}</b><br>X: {rel_x:.2f} м<br>Y: {rel_y:.2f} м<br>Z: {rel_z:.2f} м"
    v=np.array([[x,y,z],[x+dx,y,z],[x+dx,y,z+dz],[x,y,z+dz],[x,y+dy,z],[x+dx,y+dy,z],[x+dx,y+dy,z+dz],[x,y+dy,z+dz]])
    f=[[0,1,2],[0,2,3],[4,7,6],[4,6,5],[0,4,5],[0,5,1],[1,5,6],[1,6,2],[3,2,6],[3,6,7],[0,3,7],[0,7,4]]
    
    face_colors_list = [shades['bottom']]*2 + [shades['top']]*2 + \
                       [shades['front']]*2 + [shades['right']]*2 + \
                       [shades['back']]*2 + [shades['left']]*2
    fig.add_trace(go.Mesh3d(x=v[:,0],y=v[:,1],z=v[:,2],
                            i=[i[0]for i in f],j=[i[1]for i in f],k=[i[2]for i in f],
                            facecolor=face_colors_list,
                            opacity=opacity,hoverinfo='text',
                            hovertext=hover_text,
                            name=item['наименование'],
                            showlegend=False))
    if with_edges:
        e=[(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
        x_c,y_c,z_c=[],[],[]; [ (x_c.extend([v[i][0],v[j][0],None]),y_c.extend([v[i][1],v[j][1],None]),z_c.extend([v[i][2],v[j][2],None])) for i,j in e ]
        fig.add_trace(go.Scatter3d(x=x_c, y=y_c, z=z_c, mode='lines', line=dict(color=shades['edge'],width=4), hoverinfo='none', showlegend=False))

def get_color_shades(base_color):
    """Генерирует оттенки цвета для 3D-визуализации."""
    try:
        m=re.match(r"hsl\((\d+),(\d+)%,(\d+)%\)",base_color); h,s,l=[int(x) for x in m.groups()]
        return {'top':f'hsl({h},{s}%,{min(100,l+20)}%)','front':f'hsl({h},{s}%,{min(100,l+10)}%)','right':f'hsl({h},{s}%,{l}%)','left':f'hsl({h},{s}%,{max(0,l-10)}%)','back':f'hsl({h},{s}%,{max(0,l-20)}%)','bottom':f'hsl({h},{s}%,{max(0,l-30)}%)','edge':'hsl(0,0%,70%)'}
    except: return {k:base_color for k in ['top','front','right','left','back','bottom','edge']}

def add_cylinder_cargo(fig, item, cargo_space_origin, opacity=1.0):
    """Добавляет визуализацию цилиндрического груза."""
    pos=np.array(item['position']); dims = item['dims']
    orig_dims=item['размеры_исходные']; d,h=orig_dims['diameter'],orig_dims['height']; r=d/2; N=50
    lighting=dict(ambient=0.5,diffuse=0.8,roughness=0.1,specular=0.1); lightpos=dict(x=1000,y=1000,z=1000)
    # Расчет относительных координат центра
    rel_x = (pos[0] - cargo_space_origin[0]) + dims[0] / 2
    rel_y = (pos[1] - cargo_space_origin[1]) + dims[1] / 2
    rel_z = (pos[2] - cargo_space_origin[2]) + dims[2] / 2
    hover_text = f"<b>{item['наименование']}</b><br>X: {rel_x:.2f} м<br>Y: {rel_y:.2f} м<br>Z: {rel_z:.2f} м"
    dim_x, dim_y, dim_z = dims[0], dims[1], dims[2]
    orientation = None
    if abs(dim_x - d) < 1e-9 and abs(dim_y - d) < 1e-9 and abs(dim_z - h) < 1e-9: orientation = 'vertical'
    elif abs(dim_x - h) < 1e-9 and abs(dim_y - d) < 1e-9 and abs(dim_z - d) < 1e-9: orientation = 'horizontal_x'
    elif abs(dim_x - d) < 1e-9 and abs(dim_y - h) < 1e-9 and abs(dim_z - d) < 1e-9: orientation = 'horizontal_y'
    if orientation == 'vertical':
        theta=np.linspace(0,2*np.pi,N); z_cyl=np.linspace(0,h,2); t_grid,z_grid=np.meshgrid(theta,z_cyl)
        x_s=r*np.cos(t_grid)+pos[0]+r; y_s=r*np.sin(t_grid)+pos[1]+r; z_s=z_grid+pos[2]
        fig.add_trace(go.Surface(x=x_s,y=y_s,z=z_s,colorscale=[[0,item['color']],[1,item['color']]],showscale=False,hoverinfo='text',hovertext=[[hover_text for _ in range(N)] for _ in range(2)], name=item['наименование'], lighting=lighting,lightposition=lightpos, showlegend=False, opacity=opacity))
        x_c,y_c=r*np.cos(theta),r*np.sin(theta); i,j,k=np.zeros(N-2,dtype=int),np.arange(1,N-1),np.arange(2,N)
        fig.add_trace(go.Mesh3d(x=x_c+pos[0]+r,y=y_c+pos[1]+r,z=np.full(N,pos[2]+h+0.001),i=i,j=j,k=k,color=item['color'],hoverinfo='none', showlegend=False, opacity=opacity))
        fig.add_trace(go.Mesh3d(x=x_c+pos[0]+r,y=y_c+pos[1]+r,z=np.full(N,pos[2]-0.001),i=i,j=np.arange(2,N),k=np.arange(1,N-1),color=item['color'],hoverinfo='none', showlegend=False, opacity=opacity))
    elif orientation == 'horizontal_x':
        theta=np.linspace(0,2*np.pi,N); x_cyl=np.linspace(0,h,2); t_grid,x_grid=np.meshgrid(theta,x_cyl)
        y_s=r*np.cos(t_grid)+pos[1]+r; z_s=r*np.sin(t_grid)+pos[2]+r; x_s=x_grid+pos[0]
        fig.add_trace(go.Surface(x=x_s,y=y_s,z=z_s,colorscale=[[0,item['color']],[1,item['color']]],showscale=False,hoverinfo='text',hovertext=[[hover_text for _ in range(N)] for _ in range(2)], name=item['наименование'], lighting=lighting,lightposition=lightpos, showlegend=False, opacity=opacity))
        y_c,z_c=r*np.cos(theta),r*np.sin(theta); i,j,k=np.zeros(N-2,dtype=int),np.arange(1,N-1),np.arange(2,N)
        fig.add_trace(go.Mesh3d(x=np.full(N,pos[0]-0.001),y=y_c+pos[1]+r,z=z_c+pos[2]+r,i=i,j=j,k=k,color=item['color'],hoverinfo='none', showlegend=False, opacity=opacity))
        fig.add_trace(go.Mesh3d(x=np.full(N,pos[0]+h+0.001),y=y_c+pos[1]+r,z=z_c+pos[2]+r,i=i,j=np.arange(2,N),k=np.arange(1,N-1),color=item['color'],hoverinfo='none', showlegend=False, opacity=opacity))
    elif orientation == 'horizontal_y':
        theta=np.linspace(0,2*np.pi,N); y_cyl=np.linspace(0,h,2); t_grid,y_grid=np.meshgrid(theta,y_cyl)
        x_s=r*np.cos(t_grid)+pos[0]+r; z_s=r*np.sin(t_grid)+pos[2]+r; y_s=y_grid+pos[1]
        fig.add_trace(go.Surface(x=x_s,y=y_s,z=z_s,colorscale=[[0,item['color']],[1,item['color']]],showscale=False,hoverinfo='text',hovertext=[[hover_text for _ in range(N)] for _ in range(2)], name=item['наименование'], lighting=lighting,lightposition=lightpos, showlegend=False, opacity=opacity))
        x_c,z_c=r*np.cos(theta),r*np.sin(theta); i,j,k=np.zeros(N-2,dtype=int),np.arange(1,N-1),np.arange(2,N)
        fig.add_trace(go.Mesh3d(y=np.full(N,pos[1]-0.001),x=x_c+pos[0]+r,z=z_c+pos[2]+r,i=i,j=j,k=k,color=item['color'],hoverinfo='none', showlegend=False, opacity=opacity))
        fig.add_trace(go.Mesh3d(y=np.full(N,pos[1]+h+0.001),x=x_c+pos[0]+r,z=z_c+pos[2]+r,i=i,j=np.arange(2,N),k=np.arange(1,N-1),color=item['color'],hoverinfo='none', showlegend=False, opacity=opacity))
    else:
        add_box_cargo(fig, {'position': item['position'], 'dims': item['dims'], 'color': item['color'], 'наименование': item['наименование']}, cargo_space_origin, with_edges=True, opacity=opacity)

def print_detailed_report(manager, unpacked_items, packing_mode, calculation_model):
    """Выводит подробный отчет о результатах упаковки."""
    print("\n" + "="*35 + " ОТЧЕТ О РЕЗУЛЬТАТАХ УПАКОВКИ " + "="*35)
    if not manager.transport_units and not unpacked_items:
        print("Не удалось упаковать ни одной транспортной единицы и нет неразмещенных предметов."); return
    total_packed_items, total_packed_weight, total_packed_volume = 0, Decimal('0.0'), Decimal('0.0')
    for i, unit in enumerate(manager.transport_units):
        if not unit.placed_items: continue
        unit_display_name = unit.unit_name
        if unit.is_vehicle: unit_display_name += f" (ГВВ: {unit.max_total_vehicle_weight/1000:.0f} т, Грузоподъемность: {unit.payload_capacity:.0f} кг)"
        print(f"\n{i+1}. {unit_display_name}")
        unit_packed_weight = unit.total_cargo_weight
        unit_volume_capacity = unit.length * unit.width * unit.height
        unit_packed_volume = sum(Decimal(str(get_item_volume(item))) for item in unit.placed_items)
        
        print(f"  Итого в {unit.unit_name}: {len(unit.placed_items)} мест (мета-предметов), Общий вес: {unit_packed_weight:.2f} кг, Общий объем: {unit_packed_volume:.4f} м³")
        
        if unit.is_vehicle:
            print("\n  --- Распределение осевых нагрузок ---")
            compliance_result = unit.axle_calculator.check_axle_load_compliance(unit.placed_items, unit.effective_curb_weight, unit.max_total_vehicle_weight, calculation_model)
            loads_info = unit.axle_calculator.get_loads(unit.placed_items, unit.effective_curb_weight, mode=calculation_model)
            
            if '3d' in calculation_model:
                wheel_loads = loads_info.get('wheel_loads', {})
                for idx in range(int(unit.axle_calculator.params['axles'])):
                    axle_num = idx + 1
                    load_left = wheel_loads.get(f'P{axle_num}_left', 0)
                    load_right = wheel_loads.get(f'P{axle_num}_right', 0)
                    total_axle_load = load_left + load_right
                    
                    deviation_info = compliance_result['details']['axle_deviations'].get(idx, {})
                    deviation_str = ""
                    if deviation_info.get('deviation_kg', 0) > 0:
                        deviation_str = f" (+{deviation_info['deviation_kg']:.2f} кг, {deviation_info['deviation_percent']:.2f}%)"
                    
                    status = "ПРЕВЫШЕНИЕ!" if compliance_result['details']['individual_axle_exceeded'].get(idx) else "OK"
                    
                    print(f"  Ось {axle_num}: {total_axle_load:.2f} кг [Статус: {status}]{deviation_str}")
                    print(f"    - Левое колесо: {load_left:.2f} кг")
                    print(f"    - Правое колесо: {load_right:.2f} кг")
            else: # 2D model report
                for idx, load in enumerate(loads_info['total_axle_loads']):
                    deviation_info = compliance_result['details']['axle_deviations'].get(idx, {})
                    deviation_str = ""
                    if deviation_info.get('deviation_kg', 0) > 0:
                        deviation_str = f" (+{deviation_info['deviation_kg']:.2f} кг, {deviation_info['deviation_percent']:.2f}%)"
                    
                    status = "ПРЕВЫШЕНИЕ!" if compliance_result['details']['individual_axle_exceeded'].get(idx) else "OK"
                    print(f"  Ось {idx+1}: {load:.2f} кг [Статус: {status}]{deviation_str}")
            total_vehicle_weight = unit.effective_curb_weight + unit_packed_weight
            print(f"\n  Общий вес транспортного средства с грузом: {total_vehicle_weight:.2f} кг")
            if compliance_result['details']['total_weight_exceeded']:
                print("  ПРЕДУПРЕЖДЕНИЕ: Общий вес транспортного средства ПРЕВЫШАЕТ допустимые нормы!")
            
            if compliance_result['is_compliant']: print("  ИТОГ: Осевые нагрузки и общий вес в пределах нормы.")
            else: print("  ИТОГ: ВНИМАНИЕ! Обнаружены нарушения по осевым нагрузкам или общему весу.")
        print("-" * 40)
        total_packed_weight += unit_packed_weight
        total_packed_volume += unit_packed_volume
    if unpacked_items:
        print("\n--- Неразмещенные предметы ---")
        for item in unpacked_items: print(f"  - {item.get('наименование', 'Неизвестный груз')} (Вес: {item.get('вес', 'N/A')} кг)")
    print(f"\n--- Общий итог: ---")
    print(f"Общий вес размещенного груза: {total_packed_weight:.2f} кг")
    print(f"Общий объем размещенного груза: {total_packed_volume:.4f} м³")

def main_loop():
    """Основной цикл программы для взаимодействия с пользователем."""
    while True:
        print("\n" + "="*25 + " НАЧАЛО НОВОГО РАСЧЕТА " + "="*25)
        packing_mode_choice = get_validated_choice("\nВыберите режим упаковки:", {
            '1': 'Безопасный режим 3D (по колесам, макс. точность)',
            '2': 'Безопасный режим 2D (по осям, стандартный)',
            '3': 'Оптимизация плотности (быстрый, без учета осей)'
        })
        if packing_mode_choice is None: break
        calculation_model = '2d'
        if packing_mode_choice == '1':
            packing_mode = 'safe'
            calculation_model = '3d'
        elif packing_mode_choice == '2':
            packing_mode = 'safe'
            calculation_model = '2d'
        else: # '3'
            packing_mode = 'density'
            calculation_model = '2d'
        
        available_unit_types_for_precheck = []
        transport_options = {'1': 'Контейнеры', '2': 'Автомобили', '3': 'Грузовые автомобили РФ'}
        transport_type_choice = get_validated_choice("\nВыберите тип перевозки:", transport_options)
        if transport_type_choice is None: break
        
        unit_db = {}
        unit_prompt = "\nВыберите тип транспорта:"
        if transport_type_choice == '1': 
            unit_db = TRANSPORT_UNIT_DB['containers']
            unit_prompt = "\nВыберите тип контейнера:"
            if packing_mode == 'safe':
                print("ИНФО: Для контейнеров расчет осевых нагрузок не производится. Режим изменен на 'Оптимизация плотности'.")
                packing_mode = 'density'
                calculation_model = '2d'
        elif transport_type_choice == '2': unit_db = TRANSPORT_UNIT_DB['vehicles']
        elif transport_type_choice == '3': unit_db = TRANSPORT_UNIT_DB['russian_trucks']
        unit_keys = list(unit_db.keys())
        # Формируем меню с опцией "Все доступные типы"
        unit_options = {str(i+1): unit_db[key]['name'] for i, key in enumerate(unit_keys)}
        unit_options[str(len(unit_keys) + 1)] = "Все доступные типы"
        unit_choice_key = get_validated_choice(unit_prompt, unit_options)
        if unit_choice_key is None: continue
        selected_unit_info_list = []
        is_all_types_selected = unit_choice_key == str(len(unit_keys) + 1)
        if is_all_types_selected:
            selected_unit_info_list = [v for k, v in unit_db.items() if k != 'custom']
            available_unit_types_for_precheck.extend(selected_unit_info_list)
        else:
            selected_key = unit_keys[int(unit_choice_key) - 1]
            selected_unit_info = unit_db[selected_key].copy()
            
            if selected_key == 'custom':
                print("\n--- Ввод параметров пользовательского транспорта ---")
                custom_name = input("Название (или Enter): ") or "Пользовательский транспорт"
                custom_l = get_validated_float("Длина (м): ");
                if custom_l is None: continue
                custom_w = get_validated_float("Ширина (м): ");
                if custom_w is None: continue
                custom_h = get_validated_float("Высота (м): ");
                if custom_h is None: continue
                custom_weight = get_validated_float("Полная масса (GVW) или Грузоподъемность (кг): ");
                if custom_weight is None: continue
                custom_unit_info = {'name': custom_name, 'length': custom_l, 'width': custom_w, 'height': custom_h, 'max_weight': custom_weight}
                if (transport_type_choice == '2' or transport_type_choice == '3'):
                    print("\n--- Ввод параметров осей для пользовательского автомобиля ---")
                    num_axles = get_validated_int("Количество осей: ")
                    if num_axles is None: continue
                    custom_unit_info['axles'] = num_axles
                    custom_curb_axle_loads = []
                    for i in range(num_axles):
                        load = get_validated_float(f"Снаряженная масса на ось {i+1} (кг): ")
                        if load is None: continue
                        custom_curb_axle_loads.append(load)
                    custom_unit_info['curb_axle_loads'] = custom_curb_axle_loads
                    wheel_type_choice = get_validated_choice("Тип колес:", {'1': 'Односкатные', '2': 'Двускатные'})
                    if wheel_type_choice is None: continue
                    custom_unit_info['wheel_type'] = 'single' if wheel_type_choice == '1' else 'dual'
                selected_unit_info = custom_unit_info
            
            selected_unit_info_list.append(selected_unit_info)
            available_unit_types_for_precheck.append(selected_unit_info)
            
        final_calculation_model = calculation_model
        # Проверяем только первый элемент, т.к. в небезопасных режимах все ТС одного типа
        if selected_unit_info_list and 'saddle_position_x' in selected_unit_info_list[0] and calculation_model == '3d':
            print("\n--- Выбор модели расчета для автопоезда ---")
            mode_choice = get_validated_choice("Выберите метод расчета осевых нагрузок:", {
                '1': 'Точный для автопоезда (с учетом распределения на тягач и полуприцеп)',
                '2': 'Упрощенный (рассматривать как единое ТС)'
            })
            if mode_choice == '1':
                final_calculation_model = '3d_articulated'
            else:
                final_calculation_model = '3d_simple'
        elif calculation_model == '3d':
            final_calculation_model = '3d_simple'
        if selected_unit_info_list and 'axles' in selected_unit_info_list[0]:
            # Применяем доп. параметры ко всем выбранным ТС, если это список
            temp_list = []
            for unit in selected_unit_info_list:
                 unit_copy = unit.copy()
                 unit_copy = get_axle_positions_from_user(unit_copy)
                 if '3d' in final_calculation_model:
                     unit_copy = get_3d_parameters_from_user(unit_copy)
                 temp_list.append(unit_copy)
            selected_unit_info_list = temp_list
        curb_weight_override = None
        if selected_unit_info_list and packing_mode == 'safe' and 'curb_axle_loads' in selected_unit_info_list[0]:
            override_choice = get_validated_choice("\nУточнить массу снаряженного автомобиля?", {'1': 'Да', '2': 'Нет'})
            if override_choice == '1':
                curb_weight_override = get_validated_float("Введите массу снаряженного автомобиля (кг): ")
                if curb_weight_override is None: continue
        cargo_to_pack = input_cargo(available_unit_types_for_precheck, PALLET_DATABASE)
        if not cargo_to_pack:
            print("Не введено ни одного корректного груза для упаковки.")
            if get_validated_choice("\nЖелаете начать новый расчет?", {'1':'Да', '2':'Нет'}) != '1': break
            continue
        manager = PackingManager(packing_mode=packing_mode, calculation_model=final_calculation_model)
        for item in cargo_to_pack: manager.add_raw_item(item)
        try:
            unpacked_items = manager.pack_items(selected_unit_info_list, curb_weight_override)
            
            if packing_mode == 'safe' and unpacked_items:
                print("\n--- ВНИМАНИЕ: Не все предметы удалось разместить с соблюдением всех ограничений. ---")
                action_choice = get_validated_choice("Что вы хотите сделать?", {'1': 'Просмотреть текущий результат', '2': 'Начать новый расчет'})
                if action_choice == '2': continue
            print_detailed_report(manager, unpacked_items, packing_mode, final_calculation_model)
            visualize_packed_units(manager, unpacked_items)
        except Exception as e:
            print(f"\nПроизошла критическая ошибка во время упаковки: {e}")
            traceback.print_exc()
        if get_validated_choice("\nЖелаете начать новый расчет?", {'1':'Да', '2':'Нет'}) != '1': break
    print("\nРасчет завершен. До свидания!")

if __name__ == "__main__":
    main_loop(
