import numpy as np
from copy import deepcopy, copy
from lib.pattern_reading.layer import Layer
from lib.pattern_reading.print_path import PrintPath
from lib.pattern_reading.pattern import Pattern
import time


class BasePrinter:
    current_position = np.array([0, 0, 0], dtype=np.float32)
    print_time = 0
    print_distance = 0
    non_print_distance = 0

    header = ''
    body = ''
    footer = ''

    def __init__(self,
                 print_speed,
                 non_print_speed,
                 print_width,
                 layer_thickness,
                 first_layer_height,
                 physical_pixel_size=None,
                 lift_off_distance=10,
                 lift_off_height=2):
        self.print_speed = print_speed
        self.non_print_speed = non_print_speed
        self.print_width = print_width
        self.layer_thickness = layer_thickness
        self.first_layer_thickness = first_layer_height

        self.physical_pixel_size = physical_pixel_size
        self.lift_off_distance = lift_off_distance
        self.lift_off_height = lift_off_height
        self.__generate_header()
        self.start_time = time.time()

    def slice_pattern(self, pattern: Pattern, layers, **kwargs):
        self.physical_pixel_size = self.print_width / pattern.pixel_path_width
        self.comment(f"Slicing pattern \"{pattern.pattern_name}\"")
        pattern_copy = deepcopy(pattern)
        pattern_copy.scale(self.physical_pixel_size)

        if hasattr(layers, '__iter__'):
            i_layers = [layer % pattern_copy.layer_count for layer in layers]
        else:
            i_layers = [i % pattern_copy.layer_count for i in range(layers)]

        self.__z_move(kwargs.get('first_layer_thickness', self.first_layer_thickness))

        for i in i_layers:
            self.slice_layer(pattern_copy.layers[i])
            self.__z_move_incremental(self.layer_thickness)

        print(
            f"Generation of gcode for {len(i_layers)}-layered \"{pattern_copy.pattern_name}\" took "
            f"{(time.time() - self.start_time) * 1e3:.2f} ms.")

    def __generate_header(self):
        time_string = time.strftime("%a, %d %b %Y %H:%M:%S")
        self.header = "; Generated on: " + time_string + "\n"
        self.header += "; Using code version: \n"

    def comment(self, content):
        self.body += "; " + content + "\n"

    def slice_layer(self, layer: Layer):
        if self.physical_pixel_size is None:
            raise ValueError("Physical pixel size is undefined. Initialise it either by providing it during "
                             "initialisation or by slicing using a Pattern class object.")

        self.comment("Beginning a new layer.")
        for path in layer.print_paths:
            self.comment("Moving to the next path.")
            self.body += self.__non_printing_move(path.start())
            self.body += self.__slice_path(path)

    def __z_move(self, height):
        new_position = copy(self.current_position)
        new_position[2] = height
        self.__printing_move(new_position)

    def __z_move_incremental(self, displacement):
        self.__z_move(self.current_position[2] + displacement)

    def __printing_move_2d(self, position):
        self.current_position[:2] = position
        return f"G1 X{position[0]:.3f} Y{position[1]:.3f} F{self.print_speed:d}\n"

    def __printing_move_3d(self, position):
        self.current_position = position
        return f"G1 X{position[0]:.3f} Y{position[1]:.3f} Z{position[2]:.3f} F{self.print_speed:d}\n"

    def __printing_move(self, position):
        if len(position) == 2:
            return self.__printing_move_2d(position)
        elif len(position) == 3:
            return self.__printing_move_3d(position)
        else:
            raise RuntimeError(f"Invalid position given: {position} should have either 2 or 3 components.")

    def __non_printing_move(self, position):
        if len(position) == 2:
            position = np.array([position[0], position[1], self.current_position[2]])
        elif len(position) != 3:
            raise RuntimeError(f"Invalid position given: {position} should have either 2 or 3 components.")

        if self.lift_off_distance is not None and np.linalg.norm(
                position - self.current_position) >= self.lift_off_distance:
            command = f"G1 Z{self.current_position[2] + self.lift_off_height:.3f} F{self.non_print_speed:d}\n"
            move_length = self.lift_off_height

            command += f"G1 X{position[0]:.3f} Y{position[1]:.3f} F{self.non_print_speed:d}\n"
            move_length += np.linalg.norm(self.current_position[:2] - position[:2])

            command += f"G1 Z{position[2]:.3f} F{self.non_print_speed:d}\n"
            move_length += np.abs(self.current_position[2] + self.lift_off_height - position[2])
        else:
            command = f"G1 X{position[0]:.3f} Y{position[1]:.3f}  Z{position[2]:.3f}F{self.non_print_speed:d}\n"
            move_length = np.linalg.norm(self.current_position - position)
        self.current_position[:len(position)] = position
        self.non_print_distance += move_length
        self.print_time += move_length / self.non_print_speed

        return command

    def __slice_path(self, path: PrintPath):
        path_string = ''

        for position in path.path_coordinates:
            path_string += self.__printing_move(position)

        self.print_time += path.length / self.print_speed
        self.print_distance += path.length
        return path_string
