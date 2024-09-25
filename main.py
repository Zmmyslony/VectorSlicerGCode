from lib.pattern_reading.pattern import Pattern
from pathlib import Path
from lib.gcode.base_printer import BasePrinter
import numpy as np

if __name__ == '__main__':
    cwd = Path.cwd()
    pattern_path = cwd.parent.parent / "CLionProjects" / "Vector_Slicer" / "output" / "paths" / "azimuthal_10_mm.csv"

    pattern = Pattern(pattern_path)
    # pattern.move([2, 5])
    # pattern.rotate(np.pi / 3)

    printer = BasePrinter(240, 1200, 0.2, 0.120, 0.145, physical_pixel_size=0.2/9)
    printer.slice_pattern(pattern, 4, first_layer_thickness=0.24)