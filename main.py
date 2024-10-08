from lib.pattern_reading.pattern import Pattern
from pathlib import Path
from lib.gcode.base_printer import BasePrinter
from lib.gcode.prusa_printer import PrusaPrinter
from lib.gcode.hyrel_printer import HyrelPrinter
import numpy as np

if __name__ == '__main__':
    cwd = Path.cwd()
    pattern_path = cwd.parent.parent / "CLionProjects" / "Vector_Slicer" / "output" / "paths" / "azimuthal_10_mm.csv"

    # pattern = Pattern(pattern_path)
    # printer = HyrelPrinter(240, 1200, 0.2, 0.120, 1, 80e3, 80, 50)
    # printer.initial_configuration([105, 86, 0])
    # printer.slice_pattern(pattern, 4, first_layer_thickness=0.24)
    # printer.finish_print()
    # printer.export("test_hyrel.gcode")

    radial_20_mm_path = cwd.parent.parent / "CLionProjects" / "Vector_Slicer" / "output" / "paths" / "prusa_radial_20_mm.csv"
    radial_20_mm = Pattern(radial_20_mm_path)

    prusa = PrusaPrinter()
    prusa_header = open("./input/mk4s_PLA_header.txt", "r").read()
    prusa_footer = open("./input/mk4s_PLA_footer.txt", "r").read()
    prusa.slice_pattern(radial_20_mm, 8, offset=[20, 20])
    prusa.export("text_prusa.gcode", header_supplement=prusa_header, footer_supplement=prusa_footer)
