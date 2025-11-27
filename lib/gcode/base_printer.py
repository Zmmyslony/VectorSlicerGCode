#  Copyright (c) 2025, Michał Zmyślony, mlz22@cam.ac.uk.
#
#  Please cite following publication if you use any part of this code in work you publish or distribute:
#  [1] Michał Zmyślony M., Klaudia Dradrach, John S. Biggins,
#     Slicing vector fields into tool paths for additive manufacturing of nematic elastomers,
#     Additive Manufacturing, Volume 97, 2025, 104604, ISSN 2214-8604, https://doi.org/10.1016/j.addma.2024.104604.
#
#  This file is part of VectorSlicerGCode.
#
#  VectorSlicerGCode is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  VectorSlicerGCode is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
#  implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
#  Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with VectorSlicerGCode.
#  If not, see <https://www.gnu.org/licenses/>.

import random

import numpy as np
from copy import deepcopy, copy
import time
from pathlib import Path
import os

from lib.pattern_reading.layer import Layer
from lib.pattern_reading.print_path import PrintPath
from lib.pattern_reading.pattern import Pattern

VER_MAJOR = 0
VER_MINOR = 4
VER_PATCH = 1

_HEADER_FILENAME = "./tmp_header.gcode"
_BODY_FILENAME = "./tmp_body.gcode"
_FOOTER_FILENAME = "./tmp_footer.gcode"


class ExtrusionType():
    def __init__(self, is_relative=False, is_variable_width=False, is_variable_speed=False, is_volumetric=False,
                 is_native_hyrel=False):
        self.is_native_hyrel = is_native_hyrel
        self.is_relative = is_relative
        self.is_volumetric = is_volumetric
        self.is_variable_width = is_variable_width
        self.is_variable_speed = is_variable_speed


def cross_section(width, height):
    """ Follows https://manual.slic3r.org/advanced/flow-math """
    apparent_width = width + height * (1 - np.pi / 4)
    return (apparent_width - height) * height + np.pi * (height / 2) ** 2


class BasePrinter:
    """
    Base printer object that should be configured before using.
    """
    __header = None
    __body = None
    __footer = None
    __is_initialised = False

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
                 extrusion_type: ExtrusionType = ExtrusionType(),
                 retraction_length=None,
                 retraction_rate=None,
                 x_limit=None,
                 y_limit=None,
                 z_limit=None,
                 material_density=1.25):
        self._print_speed = print_speed
        self._non_print_speed = non_print_speed
        self._print_width = print_width
        self._layer_thickness = layer_thickness
        self._first_layer_thickness = layer_thickness if first_layer_height is None else first_layer_height
        self._filament_cross_section = np.pi * filament_diameter ** 2 / 4
        self._reference_cross_section = cross_section(print_width, layer_thickness)
        self.__material_density = material_density

        self.current_position = np.array([0, 0, 0], dtype=np.float32)
        self.print_time = 0
        self.print_distance = 0
        self.non_print_distance = 0
        self.extrusion_amount = 0
        self._total_extrusion_amount = 0

        self._physical_pixel_size = physical_pixel_size
        self._lift_off_distance = lift_off_distance
        self._lift_off_height = lift_off_height
        self._extrusion_multiplier = extrusion_multiplier
        self._extrusion_type = extrusion_type

        self._retraction_length = retraction_length
        self._retraction_rate = retraction_rate

        self.x_limit = x_limit
        self.y_limit = y_limit
        self.z_limit = z_limit

        # self._init()

    def _init(self):
        self._create_container_files()
        self._generate_header()
        self._start_time = time.time()
        self.__is_initialised = True

    def _create_container_files(self):
        self.__header = open(_HEADER_FILENAME, "w")
        self.__body = open(_BODY_FILENAME, "w")
        self.__footer = open(_FOOTER_FILENAME, "w")

    def _delete_container_files(self):
        os.remove(self.__header.name)
        os.remove(self.__body.name)
        os.remove(self.__footer.name)

        self.__header = None
        self.__body = None
        self.__footer = None
        self.__is_initialised = False

    def export(self, filename: str, header_supplement: str = None, body_supplement: str = None,
               footer_supplement: str = None):
        """
        Exports the sliced pattern as ./output/{filename}.csv. If supplements are provided, they are placed after
        auto-generated header/body/footer.
        :param filename: stem of the desired filename
        :param header_supplement:
        :param body_supplement:
        :param footer_supplement:
        :return:
        """
        output_directory = Path("./output")
        if not output_directory.exists(): os.mkdir(output_directory)

        seconds = int(self.print_time * 60) % 60
        minutes = int(self.print_time) % 60
        hours = int(self.print_time / 60) % 60
        self._reset_extrusion_status()

        self._comment_header(f"Total printing time: {hours:d}:{minutes:d}:{seconds:d} (excluding heating).")
        self._comment_header(f"Total printing distance: {self.print_distance:.1f} mm at {self._print_speed} mm/min.")
        self._comment_header(
            f"Total non-printing distance: {self.non_print_distance:.1f} mm at {self._non_print_speed} mm/min.")

        extrusion_amount = self._total_extrusion_amount + self.extrusion_amount
        extrusion_volume = extrusion_amount if self._extrusion_type.is_volumetric else extrusion_amount * self._filament_cross_section
        if extrusion_volume < 1000:
            self._comment_header(
                f"Total extrusion amount: {extrusion_volume:.2f} ul (approx {extrusion_volume * self.__material_density:.2f} mg).")
        else:
            self._comment_header(
                f"Total extrusion amount: {extrusion_volume / 1000:.2f} ml (approx {extrusion_volume * self.__material_density / 1000:.2f} g).")

        h_name = self.__header.name
        b_name = self.__body.name
        f_name = self.__footer.name
        self.__header.close()
        self.__body.close()
        self.__footer.close()

        f = open(output_directory / filename, 'w')
        f.write(open(h_name, "r").read())
        if header_supplement is not None: f.write(header_supplement)

        f.write(open(b_name, "r").read())
        if body_supplement is not None: f.write(body_supplement)

        f.write(open(f_name, "r").read())
        if footer_supplement is not None: f.write(footer_supplement)
        f.close()

        self._delete_container_files()

    def slice_pattern(self, pattern: Pattern, layers: int, position: list, **kwargs):
        """
        Slices the pattern
        :param pattern:
        :param layers: Number of layers to generate the output with.
        :param position: Position in mm to which the pattern should be moved. Usually, the pattern extends from [0, 0] in positive direction.
        :param kwargs:
        :return:
        """
        if layers <= 0:
            raise RuntimeError("Pattern cannot be sliced with non-positive number of layers.")
        if not self.__is_initialised:
            self._init()
        self._start_time = time.time()

        self._physical_pixel_size = self._print_width / pattern.pixel_path_width
        self._comment_body(f"Slicing pattern \"{pattern.pattern_name}\"")
        pattern_copy = deepcopy(pattern)
        pattern_copy.scale(self._physical_pixel_size)
        if position is not None:
            pattern_copy.move(position)

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

    def slice_layer(self, layer: Layer, speed=None):
        if self._physical_pixel_size is None:
            raise ValueError("Physical pixel size is undefined. Initialise it either by providing it during "
                             "initialisation or by slicing using a Pattern class object.")

        self._comment_body("Beginning a new layer.")
        if np.linalg.norm(self.current_position[:2] - layer.get_end()) < np.linalg.norm(
                self.current_position[:2] - layer.get_beginning()):
            layer.invert()

        for path in layer.print_paths:
            self._comment_body("Moving to the next path.")
            self._non_printing_move(path.start())
            self._slice_path(path, speed=speed)

    def _set_absolute_extrusion(self):
        self._is_extrusion_absolute = True
        self._comment_body("Setting absolute E-values")
        self._command_body("M82")

    def _reset_extrusion_status(self):
        self._total_extrusion_amount += self.extrusion_amount
        self.extrusion_amount = 0
        self._command_body("G92 E0")

    def _set_relative_extrusion(self):
        self._is_extrusion_absolute = False
        self._comment_body("Setting relative E-values")
        self._command_body("M83")

    def _generate_header(self):
        time_string = time.strftime("%a, %d %b %Y %H:%M:%S")
        self._comment_header(f"File generated using VectorSlicerGCode version: {VER_MAJOR}.{VER_MINOR}.{VER_PATCH}.")
        self._comment_header(f"Generated on: {time_string}.")

    def _dwell(self, s=None, ms=None):
        if s is not None:
            self._command_body(f"G4 S{s:d}")
            self.print_time += s / 60
            return
        if ms is not None:
            self._command_body(f"G4 P{ms:d}")
            self.print_time += ms / 1000 / 60
            return
        else:
            raise RuntimeWarning("No dwell time specified.")

    def _break_header(self):
        self.__header.write("\n")

    def _break_body(self):
        self.__body.write("\n")

    def _comment_body(self, content):
        self.__body.write(f"; {content}\n")

    def _comment_header(self, content):
        self.__header.write(f"; {content}\n")

    def _comment_footer(self, content):
        self.__footer.write(f"; {content}\n")

    def _command_body(self, content):
        self.__body.write(f"{content}\n")

    def _commented_command_body(self, command, comment):
        self.__body.write(f"{command}; {comment}\n")

    def _command_header(self, content):
        self.__header.write(f"{content}\n")

    def _command_footer(self, content):
        self.__footer.write(f"{content}\n")

    def _z_move(self, height, speed=None):
        new_position = copy(self.current_position)
        new_position[2] = height
        self._non_printing_move(new_position, speed=speed)

    def _z_move_incremental(self, displacement, speed=None):
        self._z_move(self.current_position[2] + displacement, speed)

    def _printing_move_3d_variable_width(self, position, width, speed=None):
        length = np.linalg.norm(position - self.current_position)
        path_cross_section = cross_section(width, self._layer_thickness)
        if self._extrusion_type.is_volumetric:
            extrusion_amount = length * path_cross_section * self._extrusion_multiplier
        else:
            extrusion_amount = length * path_cross_section / self._filament_cross_section * self._extrusion_multiplier

        self.extrusion_amount += extrusion_amount
        print_speed = self._print_speed if speed is None else speed

        if self._extrusion_type.is_variable_speed:
            print_speed *= self._reference_cross_section / path_cross_section

        self.print_distance += length
        self.print_time += length / print_speed
        command = f"G1 X{position[0]:.3f} Y{position[1]:.3f} Z{position[2]:.3f}"
        if self._extrusion_type.is_native_hyrel:
            command += " E1"
        elif self._extrusion_type.is_relative:
            command += f" E{extrusion_amount:.5f}"
        else:
            command += f" E{self.extrusion_amount:.5f}"

        command += f" F{print_speed:.0f}"
        self.current_position = position
        self._command_body(command)

    def __printing_move_constant_width_constant_speed(self, position, speed=None):
        length = np.linalg.norm(position - self.current_position)

    def __is_position_in_bounds(self, position):
        if (
                (self.x_limit is not None and position[0] > self.x_limit) or
                (self.y_limit is not None and position[1] > self.y_limit) or
                (self.z_limit is not None and position[2] > self.z_limit) or
                position[0] < 0 or position[1] < 0 or position[2] < 0
        ):
            raise RuntimeError(
                f"Position {position} is out of bounds [{self.x_limit}, {self.y_limit}, {self.z_limit}] .")

    def __printing_move_base(self, position, extrusion_multiplier, speed):
        self.__is_position_in_bounds(position)

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
        if width is not None and self._extrusion_type.is_variable_width:
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

        self.__is_position_in_bounds(position)

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
        comment = "Switching to relative positioning."
        command = "G91"

        self._commented_command_body(command, comment)

    def _set_absolute_positioning(self):
        comment = "Switching to absolute positioning."
        command = "G90"
        self._commented_command_body(command, comment)

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
            if path.overlap is None or not self._extrusion_type.is_variable_width:
                self._printing_move(position, speed=speed)
            else:
                width = self._print_width * (1 - path.overlap[i] / 2)
                self._printing_move_variable_width(position, width, speed=speed)

    def import_header(self, header_path):
        header_file = open(header_path, 'r')
        self.__header += header_file.read()

    def import_footer(self, footer_path):
        footer_file = open(footer_path, 'r')
        self.__footer += footer_file.read()

    def _empty_containers(self):
        self.__header = ""
        self.__body = ""
        self.__footer = ""
