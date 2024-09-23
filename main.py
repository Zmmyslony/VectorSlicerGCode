from lib.pattern_reading.pattern import Pattern
from pathlib import Path
import numpy as np

if __name__ == '__main__':
    cwd = Path.cwd()
    pattern_path = cwd.parent.parent / "CLionProjects" / "Vector_Slicer" / "output" / "paths" / "azimuthal_10_mm.csv"

    pattern = Pattern(pattern_path)

    print(pattern.layers[0].print_paths[0].path_coordinates[-1], pattern.bounds)
    pattern.move([2, 5])
    print(pattern.layers[0].print_paths[0].path_coordinates[-1], pattern.bounds)
    pattern.rotate(np.pi / 3)
    print(pattern.layers[0].print_paths[0].path_coordinates[-1], pattern.bounds)