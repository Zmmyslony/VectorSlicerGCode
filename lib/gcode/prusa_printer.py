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

from lib.gcode.base_printer import BasePrinter, ExtrusionType
import numpy as np


class PrusaPrinter(BasePrinter):
    """
    Base configuration of Prusa's MK4S printer which uses PLA and variable width, i.e. extruded width ranges between
    0.4 to 0.8 mm to accommodate for the divergences in the director pattern.
    """
    def __init__(self, print_speed=2400, non_print_speed=18000, print_width=0.8, layer_thickness=0.2,
                 lift_off_distance=5, lift_off_height=0.8, filament_diameter=1.75):
        BasePrinter.__init__(self, print_speed, non_print_speed, print_width, layer_thickness,
                             lift_off_distance=lift_off_distance, lift_off_height=lift_off_height,
                             filament_diameter=filament_diameter,
                             extrusion_type=ExtrusionType(is_variable_width=True, is_variable_speed=True,
                                                          is_relative=True),
                             retraction_rate=1500, retraction_length=1, x_limit=250, y_limit=210, z_limit=220)
