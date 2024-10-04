from pathlib import Path
from lib.pattern_reading.print_path import PrintPath
from lib.pattern_reading.layer import Layer


def read_pattern(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    overlap_path = path.parent.parent / "overlap" / f"{path.stem}.csv"
    overlap_content = overlap_path.read_text(encoding="utf_8") if overlap_path.exists else None
    raw_content = path.read_text(encoding="utf_8")
    return raw_content, overlap_content


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
