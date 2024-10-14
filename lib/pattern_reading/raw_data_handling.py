from pathlib import Path
from lib.pattern_reading.print_path import PrintPath
from lib.pattern_reading.layer import Layer
import os


def search_for_output_directory(depth, silent=True):
    if not silent: print(f"Searching for output directory at depth {depth}")
    parents = Path.cwd().parents
    root = parents[depth if depth < len(parents) else -1]
    for roots, dirs, files in os.walk(root):
        for dir in dirs:
            dir_parent = Path(roots).stem

            if (dir_parent.lower() == "vector_slicer" or dir_parent.lower() == "vectorslicer") and dir.lower() == "output":
                return os.path.join(roots, dir)
    if not silent: print(f"Output directory not found at depth {depth}")
    return None


def find_vector_slicer_directory(silent=True):
    vector_slicer_api = os.environ.get('VECTOR_SLICER_API')
    vector_slicer_output = os.environ.get('VECTOR_SLICER_OUTPUT')

    if vector_slicer_output is not None:
        if not silent: print(f"Found output directory at {vector_slicer_output}")
        return Path(vector_slicer_output)
    else:
        for depth in range(4):
            found_directory = search_for_output_directory(depth)
            if found_directory is not None:
                if not silent: print(f"Found output directory at {found_directory}")
                return found_directory
    raise RuntimeError("Could not find the output directory. Ensure that VECTOR_SLICER_OUTPUT environment variable is "
                       "correctly set, or the VectorSlicerGCode and Vector Slicer share a parent (or 2-nd level parent)"
                       " directory.")


def read_pattern(pattern_name=str):
    vector_slicer_output = os.path.Path(find_vector_slicer_directory())
    paths = vector_slicer_output / "paths" / f"{pattern_name}.csv"
    if not paths.exists(): raise FileNotFoundError(f"File not found: {paths}")
    overlap = vector_slicer_output / "overlap" / f"{pattern_name}.csv"
    overlap_content = overlap.read_text(encoding="utf_8") if overlap.exists() else None
    paths_content = paths.read_text(encoding="utf_8")
    return paths_content, overlap_content


def find_key_data(string, parameter_key):
    matched_lines = [line for line in string.split('\n') if parameter_key in line]

    if len(matched_lines) == 0:
        raise ValueError('Missing key {}'.format(parameter_key))
    if len(matched_lines) > 1:
        raise ValueError('Multiple matches for a key {}'.format(parameter_key))

    data = matched_lines[0].split(':')[-1].strip()
    return data


def _is_creation_date_same(first_content, second_content):
    if first_content is None or second_content is None:
        print("Overlap data missing. Variable width printing will be disabled.")
        return False
    first_creation_date = find_key_data(first_content, "Creation date")
    second_creation_date = find_key_data(second_content, "Creation date")
    if first_creation_date == second_creation_date:
        return True
    else:
        print("Path and overlap files have different creation time.")
        return False


def __read_into_layer_list(raw_data):
    start = '# Start of pattern'
    end = '# End of pattern'
    layer_list = []
    print_paths = []
    is_reading_on = False
    for line in raw_data.split('\n'):
        if line == start:
            is_reading_on = True
        elif line == end:
            is_reading_on = False
            layer_list.append(print_paths)
            print_paths = []
        elif is_reading_on:
            print_paths.append(line)
    return layer_list


def read_layers(layer_data, overlap_data):
    coordinates = __read_into_layer_list(layer_data)
    overlaps = __read_into_layer_list(overlap_data) if _is_creation_date_same(layer_data, overlap_data) else None
    layers = []
    for i in range(len(coordinates)):
        paths = []
        for j in range(len(coordinates[i])):
            if overlaps is not None:
                path = PrintPath(coordinates[i][j], overlap=overlaps[i][j])
            else:
                path = PrintPath(coordinates[i][j])
            paths.append(path)
        layers.append(Layer(paths))
        paths = []

    return layers
