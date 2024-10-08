import random

import numpy as np
from copy import deepcopy, copy
from lib.pattern_reading.layer import Layer
from lib.pattern_reading.print_path import PrintPath
from lib.pattern_reading.pattern import Pattern
import time
from pathlib import Path
import os

VER_MAJOR = 0
VER_MINOR = 2
VER_PATCH = 2

_HEADER_FILENAME = "./tmp_header.gcode"
_BODY_FILENAME = "./tmp_body.gcode"
_FOOTER_FILENAME = "./tmp_footer.gcode"

_EXT_ONOFF = 0
"Extrusion is simply switched on or off using E1 or E0"
_EXT_ABS_CONST = 1
"Extrusion is controlled based on absolute E, with constant width and constant speed."
_EXT_REL_CONST = 2
"Extrusion is controlled based on relative E, with constant width and constant speed."
_EXT_ABS_VAR = 3
"Extrusion is controlled based on absolute E, with variable width and constant speed."
_EXT_REL_VAR = 4
"Extrusion is controlled based on relative E, with variable width and constant speed."
_EXT_ABS_VAR_SPEED = 5
"Extrusion is controlled based on absolute E, with variable width and variable speed, keeping extrusion rate constant."
_EXT_REL_VAR_SPEED = 6
"Extrusion is controlled based on relative E, with variable width and variable speed, keeping extrusion rate constant."

_EXT_WITH_VAR_SPEED = [_EXT_ABS_VAR_SPEED, _EXT_REL_VAR_SPEED]
"Extrusion types where printing speed is used to control the extrusion width. "
_EXT_WITH_CONST_W = [_EXT_ABS_CONST, _EXT_REL_CONST, _EXT_ONOFF]
"Extrusion types where print width is constant. "
_EXT_WITH_VAR_W = [_EXT_ABS_VAR, _EXT_REL_VAR, _EXT_ABS_VAR_SPEED, _EXT_REL_VAR_SPEED]
"Extrusion types where print width is variable"
_EXT_WITH_REL_E = [_EXT_REL_CONST, _EXT_REL_VAR, _EXT_REL_VAR_SPEED]
"Extrusion types where the extrusion is controlled by relative E value."
_EXT_WITH_ABS_E = [_EXT_ABS_VAR, _EXT_ABS_CONST, _EXT_ABS_VAR_SPEED]
"Extrusion types where the extrusion is controlled by absolute E value."

ExtrusionTypes = dict(
    OnOff=_EXT_ONOFF,
    AbsoluteConstantWidth=_EXT_ABS_CONST,
    RelativeConstantWidth=_EXT_REL_CONST,
    AbsoluteVariableWidth=_EXT_ABS_VAR,
    RelativeVariableWidth=_EXT_REL_VAR,
    AbsoluteVariableWidthSpeed=_EXT_ABS_VAR_SPEED,
    RelativeVariableWidthSpeed=_EXT_REL_VAR_SPEED
)


def cross_section(width, height):
    """ Follows https://manual.slic3r.org/advanced/flow-math """
    apparent_width = width + height * (1 - np.pi / 4)
    return (apparent_width - height) * height + np.pi * (height / 2) ** 2


class BasePrinter:
    def __init__(self,
                 print_speed,
                 non_print_speed,
                 print_width,
                 layer_thickness,
                 first_layer_height=None,
                 physical_pixel_size=None,
                 lift_off_distance=10,
                 lift_off_height=2,
                 extrusion_multiplier=1,
                 filament_diameter=1.75,
                 extrusion_control_type: int = ExtrusionTypes['RelativeConstantWidth'],
                 retraction_length=None,
                 retraction_rate=None):
        self._print_speed = print_speed
        self._non_print_speed = non_print_speed
        self._print_width = print_width
        self._layer_thickness = layer_thickness
        self._first_layer_thickness = layer_thickness if first_layer_height is None else first_layer_height
        self._filament_cross_section = np.pi * filament_diameter ** 2 / 4
        self._reference_cross_section = cross_section(print_width, layer_thickness)

        rand = f"{random.random() * 1e6:.0f}"
        self.header = open(_HEADER_FILENAME + rand, "w")
        self.body = open(_BODY_FILENAME + rand, "w")
        self.footer = open(_FOOTER_FILENAME + rand, "w")

        self.current_position = np.array([0, 0, 0], dtype=np.float32)
        self.print_time = 0
        self.print_distance = 0
        self.non_print_distance = 0
        self.extrusion_distance = 0
        self._total_extrusion_distance = 0

        self._physical_pixel_size = physical_pixel_size
        self._lift_off_distance = lift_off_distance
        self._lift_off_height = lift_off_height
        self._generate_header()
        self._start_time = time.time()
        self._extrusion_multiplier = extrusion_multiplier
        self._extrusion_control_type = extrusion_control_type

        self._retraction_length = retraction_length
        self._retraction_rate = retraction_rate

        self._is_extrusion_on_off = self._extrusion_control_type == _EXT_ONOFF
        self._is_extrusion_absolute = self._extrusion_control_type in _EXT_WITH_ABS_E
        self._is_width_variable = self._extrusion_control_type in _EXT_WITH_VAR_W
        self._is_speed_variable = self._extrusion_control_type in _EXT_WITH_VAR_SPEED

    def _reset_extrusion_status(self):
        self._total_extrusion_distance += self.extrusion_distance
        self.extrusion_distance = 0
        self._command_body("G92 E0")

    def export(self, filename, header_supplement=None, body_supplement=None, footer_supplement=None):
        seconds = int(self.print_time * 60) % 60
        minutes = int(self.print_time) % 60
        hours = int(self.print_time / 60) % 60
        self._reset_extrusion_status()

        self._comment_header(f"Total printing time: {hours:d}:{minutes:d}:{seconds:d} (excluding heating).")
        self._comment_header(f"Total printing distance: {self.print_distance:.1f} mm at {self._print_speed} mm/min.")
        self._comment_header(
            f"Total non-printing distance: {self.non_print_distance:.1f} mm at {self._non_print_speed} mm/min.")

        h_name = self.header.name
        b_name = self.body.name
        f_name = self.footer.name
        self.header.close()
        self.body.close()
        self.footer.close()

        f = open(Path("./output") / filename, 'w')
        f.write(open(h_name, "r").read())
        if header_supplement is not None: f.write(header_supplement)

        f.write(open(b_name, "r").read())
        if body_supplement is not None: f.write(body_supplement)

        f.write(open(f_name, "r").read())
        if footer_supplement is not None: f.write(footer_supplement)
        f.close()

        os.remove(h_name)
        os.remove(b_name)
        os.remove(f_name)

    def slice_pattern(self, pattern: Pattern, layers, offset=None, **kwargs):
        """
        Slices the pattern
        :param pattern:
        :param layers: Number of layers to generate the output with.
        :param offset: Position in mm to which the pattern should be moved. Usually, the pattern extends from [0, 0] in positive direction.
        :param kwargs:
        :return:
        """
        self._physical_pixel_size = self._print_width / pattern.pixel_path_width
        self._comment_body(f"Slicing pattern \"{pattern.pattern_name}\"")
        pattern_copy = deepcopy(pattern)
        pattern_copy.scale(self._physical_pixel_size)
        if offset is not None:
            pattern_copy.move(offset)

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

    def _set_absolute_extrusion(self):
        self._is_extrusion_absolute = True
        self._comment_body("Setting absolute E-values")
        self._command_body("M82")

    def _set_relative_extrusion(self):
        self._is_extrusion_absolute = False
        self._comment_body("Setting relative E-values")
        self._command_body("M83")

    def _generate_header(self):
        time_string = time.strftime("%a, %d %b %Y %H:%M:%S")
        self._comment_header(f"File generated using VectorSlicerGCode version: {VER_MAJOR}.{VER_MINOR}.{VER_PATCH}.")
        self._comment_header(f"Generated on: {time_string}.")

    def _break_header(self):
        self.header.write("\n")

    def _break_body(self):
        self.body.write("\n")

    def _comment_body(self, content):
        self.body.write(f"; {content}\n")

    def _comment_header(self, content):
        self.header.write(f"; {content}\n")

    def _comment_footer(self, content):
        self.footer.write(f"; {content}\n")

    def _command_body(self, content):
        self.body.write(f"{content}\n")

    def _command_header(self, content):
        self.header.write(f"{content}\n")

    def _command_footer(self, content):
        self.footer.write(f"{content}\n")

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

    def _printing_move_3d_variable_width(self, position, width, speed=None):
        length = np.linalg.norm(position - self.current_position)
        path_cross_section = cross_section(width, self._layer_thickness)
        extrusion_amount = length * path_cross_section / self._filament_cross_section * self._extrusion_multiplier

        self.extrusion_distance += extrusion_amount
        print_speed = self._print_speed if speed is None else speed

        if self._is_speed_variable:
            print_speed *= self._reference_cross_section / path_cross_section

        self.print_distance += length
        self.print_time += length / print_speed
        command = f"G1 X{position[0]:.3f} Y{position[1]:.3f} Z{position[2]:.3f}"
        if self._extrusion_control_type in _EXT_WITH_ABS_E:
            command += f" E{self.extrusion_distance:.5f}"
        elif self._extrusion_control_type in _EXT_WITH_REL_E:
            command += f" E{extrusion_amount:.5f}"
        else:
            command += " E1"

        command += f" F{print_speed:.0f}"
        self.current_position = position
        self._command_body(command)

    def __printing_move_constant_width_constant_speed(self, position, speed=None):
        length = np.linalg.norm(position - self.current_position)

    def __printing_move_base(self, position, extrusion_multiplier, speed):
        length = np.linalg.norm(position - self.current_position)
        extrusion = length * extrusion_multiplier
        self._current_position = position
        self._command_body(f"G1 X{position[0]:.3f} Y{position[1]:.3f} Z{position[2]:.3f} E{extrusion:.5f} F{speed:.0f}")

    def _printing_move_variable_width(self, position, width, speed=None):
        if len(position) == 2:
            position = np.concatenate([position, [self.current_position[2]]])
        elif len(position) != 3:
            raise ValueError("Position must be 2- or 3-dimensional vector")

        return self._printing_move_3d_variable_width(position, width, speed=speed)

    def _printing_move_constant_width(self, position, speed=None):
        return self._printing_move_variable_width(position, self._print_width, speed=speed)

    def _printing_move(self, position, speed=None, width=None):
        if width is not None and self._extrusion_control_type in _EXT_WITH_VAR_W:
            return self._printing_move_variable_width(position, self._print_width, speed=speed)
        else:
            return self._printing_move_constant_width(position, speed=speed)

    def _printing_move_relative(self, displacement, speed=None):
        if len(displacement) == 2:
            displacement = np.concatenate([displacement, [0]])
        elif len(displacement) != 3:
            raise ValueError("Position must be 2- or 3-dimensional vector")
        return self._printing_move(displacement + self.current_position, speed=speed)

    def _non_printing_move(self, position, speed=None):
        if speed is None: speed = self._non_print_speed
        position = np.array(position)
        if len(position) == 2:
            position = np.array([position[0], position[1], self.current_position[2]])
        elif len(position) != 3:
            raise RuntimeError(f"Invalid position given: {position} should have either 2 or 3 components.")

        if self._retraction_length is not None and self._retraction_rate is not None:
            self._command_body(f"G1 E{-self._retraction_length:.5F} F{self._retraction_rate:.0f}")
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

        if self._retraction_length is not None and self._retraction_rate is not None:
            self._command_body(f"G1 E{self._retraction_length:.5F} F{self._retraction_rate:.0f}")

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

        for i, position in enumerate(path.path_coordinates):
            if path.overlap is None or self._extrusion_control_type in _EXT_WITH_CONST_W:
                self._printing_move(position, speed=speed)
            else:
                width = self._print_width * (1 - path.overlap[i] / 2)
                self._printing_move_variable_width(position, width, speed=speed)

    def import_header(self, header_path):
        header_file = open(header_path, 'r')
        self.header += header_file.read()

    def import_footer(self, footer_path):
        footer_file = open(footer_path, 'r')
        self.footer += footer_file.read()
