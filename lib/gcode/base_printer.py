import numpy as np
from copy import deepcopy, copy
from lib.pattern_reading.layer import Layer
from lib.pattern_reading.print_path import PrintPath
from lib.pattern_reading.pattern import Pattern
import time
from pathlib import Path

VER_MAJOR = 0
VER_MINOR = 1
VER_PATCH = 0


class BasePrinter:
    current_position = np.array([0, 0, 0], dtype=np.float32)
    print_time = 0
    print_distance = 0
    non_print_distance = 0
    extrusion_distance = 0

    header = ''
    body = ''
    footer = ''

    def __init__(self,
                 print_speed,
                 non_print_speed,
                 print_width,
                 layer_thickness,
                 first_layer_height=None,
                 physical_pixel_size=None,
                 lift_off_distance=10,
                 lift_off_height=2,
                 is_extrusion_distance_based=True,
                 extrusion_multiplier=1,
                 is_extrusion_axis_absolute=True):
        self._print_speed = print_speed
        self._non_print_speed = non_print_speed
        self._print_width = print_width
        self._layer_thickness = layer_thickness
        self._first_layer_thickness = layer_thickness if first_layer_height is None else first_layer_height

        self._physical_pixel_size = physical_pixel_size
        self._lift_off_distance = lift_off_distance
        self._lift_off_height = lift_off_height
        self._generate_header()
        self._start_time = time.time()
        self._is_extrusion_distance_based = is_extrusion_distance_based
        self._extrusion_multiplier = extrusion_multiplier
        self._is_extrusion_axis_absolute = is_extrusion_axis_absolute

    def export(self, filename, header_supplement=None, body_supplement=None, footer_supplement=None):
        seconds = int(self.print_time * 60) % 60
        minutes = int(self.print_time) % 60
        hours = int(self.print_time / 60) % 60

        self._comment_header(f"Total printing time: {hours:d}:{minutes:d}:{seconds:d} (excluding heating).")
        self._comment_header(f"Total printing distance: {self.print_distance:.1f} mm at {self._print_speed} mm/min.")
        self._comment_header(
            f"Total non-printing distance: {self.non_print_distance:.1f} mm at {self._non_print_speed} mm/min.")

        f = open(Path("./output") / filename, 'w')
        f.write(self.header)
        if header_supplement is not None: f.write(header_supplement)
        f.write("\n")
        f.write(self.body)
        if body_supplement is not None: f.write(body_supplement)
        f.write("\n")
        f.write(self.footer)
        if footer_supplement is not None: f.write(footer_supplement)
        f.close()

    def slice_pattern(self, pattern: Pattern, layers, **kwargs):
        self._physical_pixel_size = self._print_width / pattern.pixel_path_width
        self._comment_body(f"Slicing pattern \"{pattern.pattern_name}\"")
        pattern_copy = deepcopy(pattern)
        pattern_copy.scale(self._physical_pixel_size)

        if hasattr(layers, '__iter__'):
            i_layers = [layer % pattern_copy.layer_count for layer in layers]
        else:
            i_layers = [i % pattern_copy.layer_count for i in range(layers)]

        self._z_move(kwargs.get('first_layer_thickness', self._first_layer_thickness))

        for i, i_layer in enumerate(i_layers):
            self.slice_layer(pattern_copy.layers[i_layer])
            self.interlayer_function(i, **kwargs)
            self._z_move_incremental(self._layer_thickness)

        print(
            f"Generation of gcode for {len(i_layers)}-layered \"{pattern_copy.pattern_name}\" took "
            f"{(time.time() - self._start_time) * 1e3:.2f} ms.")

    def interlayer_function(self, layer_index, **kwargs):
        """
        Placeholder function for child classes to introduce specific interlayer behaviour.
        :return:
        """
        return

    def _generate_header(self):
        time_string = time.strftime("%a, %d %b %Y %H:%M:%S")
        self._comment_header(f"File generated using VectorSlicerGCode version: {VER_MAJOR}.{VER_MINOR}.{VER_PATCH}.")
        self._comment_header(f"Generated on: {time_string}.")

    def _break_header(self):
        self.header += "\n"

    def _break_body(self):
        self.body += "\n"

    def _comment_body(self, content):
        self.body += "; " + content + "\n"

    def _comment_header(self, content):
        self.header += "; " + content + "\n"

    def _comment_footer(self, content):
        self.footer += "; " + content + "\n"

    def _command_body(self, content):
        self.body += content + "\n"

    def _command_header(self, content):
        self.header += content + "\n"

    def _command_footer(self, content):
        self.footer += content + "\n"

    def slice_layer(self, layer: Layer, speed=None):
        if self._physical_pixel_size is None:
            raise ValueError("Physical pixel size is undefined. Initialise it either by providing it during "
                             "initialisation or by slicing using a Pattern class object.")

        self._comment_body("Beginning a new layer.")
        for path in layer.print_paths:
            self._comment_body("Moving to the next path.")
            self._non_printing_move(path.start())
            self._slice_path(path, speed=speed)

    def _z_move(self, height, speed=None):
        new_position = copy(self.current_position)
        new_position[2] = height
        self._non_printing_move(new_position, speed=speed)

    def _z_move_incremental(self, displacement, speed=None):
        self._z_move(self.current_position[2] + displacement, speed)

    def _printing_move_2d_relative(self, displacement, speed=None):
        self._printing_move_2d(self.current_position[:2] + np.array(displacement), speed=speed)

    def _printing_move_2d(self, position, speed=None):
        new_pos = np.concatenate([position, [self.current_position[2]]])
        self._printing_move_3d(new_pos, speed=speed)

    def _printing_move_3d(self, position, speed=None):
        print_speed = self._print_speed if speed is None else speed
        if self._is_extrusion_distance_based:
            distance = np.linalg.norm(position - self.current_position)
            extrusion_amount = distance * self._extrusion_multiplier
            self.extrusion_distance += extrusion_amount
            self._command_body(
                f"G1 X{position[0]:.3f} Y{position[1]:.3f} Z{position[2]:.3f} E{self.extrusion_distance if self._is_extrusion_axis_absolute else extrusion_amount :.5f}F{print_speed:d}")
        else:
            self._command_body(
                f"G1 X{position[0]:.3f} Y{position[1]:.3f} Z{position[2]:.3f} F{print_speed:d}")
        self.current_position = position

    def _printing_move(self, position, speed=None):
        if len(position) == 2:
            return self._printing_move_2d(position, speed=speed)
        elif len(position) == 3:
            return self._printing_move_3d(position, speed=speed)
        else:
            raise RuntimeError(f"Invalid position given: {position} should have either 2 or 3 components.")

    def _non_printing_move(self, position, speed=None):
        if speed is None: speed = self._non_print_speed
        position = np.array(position)
        if len(position) == 2:
            position = np.array([position[0], position[1], self.current_position[2]])
        elif len(position) != 3:
            raise RuntimeError(f"Invalid position given: {position} should have either 2 or 3 components.")

        if (
                self._lift_off_distance is not None and
                np.linalg.norm(position - self.current_position) >= self._lift_off_distance and
                position[2] == self.current_position[2]
        ):
            self._command_body(f"G0 Z{self.current_position[2] + self._lift_off_height:.3f} F{speed:.0f}")
            move_length = self._lift_off_height

            self._command_body(f"G0 X{position[0]:.3f} Y{position[1]:.3f} F{speed:.0f}")
            move_length += np.linalg.norm(self.current_position[:2] - position[:2])

            self._command_body(f"G0 Z{position[2]:.3f} F{speed:.0f}")
            move_length += np.abs(self.current_position[2] + self._lift_off_height - position[2])
        else:
            self._command_body(f"G0 X{position[0]:.3f} Y{position[1]:.3f} Z{position[2]:.3f} F{speed:.0f}")
            move_length = np.linalg.norm(self.current_position - position)
        self.current_position[:len(position)] = position
        self.non_print_distance += move_length
        self.print_time += move_length / speed

    def _non_printing_move_relative(self, displacement, speed=None):
        displacement = np.array(displacement)
        if len(displacement) == 2:
            displacement = np.concatenate([displacement, [0]])
        self._non_printing_move(self.current_position + displacement, speed=speed)

    def _set_relative_positioning(self):
        self._comment_body("Switching to relative positioning.")
        self._command_body("G91")

    def _set_absolute_positioning(self):
        self._comment_body("Switching to absolute positioning.")
        self._command_body("G90")

    def _home_2d(self):
        self._break_body()
        self._comment_body("Homing.")
        self._set_relative_positioning()
        self._non_printing_move([0, 0, 10])
        self._set_absolute_positioning()
        self._command_body("G28 X0 Y0")
        self.current_position[0] = 0
        self.current_position[1] = 0

    def _home_3d(self):
        self._break_body()
        self._comment_body("Homing.")
        self._set_relative_positioning()
        self._non_printing_move([0, 0, 10])
        self._set_absolute_positioning()
        self._command_body("G28 X0 Y0 Z0")
        self.current_position = np.array([0, 0, 0])

    def _slice_path(self, path: PrintPath, speed=None):
        if speed is None: speed = self._print_speed

        for position in path.path_coordinates:
            self._printing_move(position, speed=speed)

        self.print_time += path.length / speed
        self.print_distance += path.length

    def import_header(self, header_path):
        header_file = open(header_path, 'r')
        self.header += header_file.read()

    def import_footer(self, footer_path):
        footer_file = open(footer_path, 'r')
        self.footer += footer_file.read()
