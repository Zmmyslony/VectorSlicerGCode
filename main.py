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

from lib.pattern_reading.pattern import Pattern
from lib.gcode.prusa_printer import PrusaPrinter
from lib.gcode.hyrel_printer import HyrelPrinter


## Example of how to use the generator to gcode files compatible with Hyrel 30M printer.
def example_hyrel_30m(pattern_name):
    printer = HyrelPrinter(240, 1200, 0.2, 0.100, 1, 80, 50, [100, 90, 0])
    printer.slice_pattern(pattern_name, 4, [0, 10])
    printer.export(f"{pattern_name}_hyrel.gcode")


## Example of how to use the generator to gcode files compatible with Prusa MK4s printer using PLA.
def example_prusa_mk4s(pattern_name):
    prusa = PrusaPrinter()
    # The header and footer are taken from pre-generated files.
    prusa_header = open("./input/mk4s_PLA_header.txt", "r").read()
    prusa_footer = open("./input/mk4s_PLA_footer.txt", "r").read()
    prusa.slice_pattern(pattern_name, 8, [20, 20])

    prusa.export(f"{pattern_name}_mk4s.gcode", header_supplement=prusa_header, footer_supplement=prusa_footer)


if __name__ == '__main__':
    example_hyrel_30m("radial_r_5_mm")
    example_prusa_mk4s("radial_r_5_mm")
