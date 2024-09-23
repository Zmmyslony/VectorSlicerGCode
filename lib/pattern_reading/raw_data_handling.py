from pathlib import Path
from lib.pattern_reading.print_path import PrintPath
from lib.pattern_reading.layer import Layer


def read_pattern(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    raw_content = path.read_text(encoding="utf_8")
    return raw_content


def find_key_data(string, parameter_key):
    matched_lines = [line for line in string.split('\n') if parameter_key in line]

    if len(matched_lines) == 0:
        raise ValueError('Missing key {}'.format(parameter_key))
    if len(matched_lines) > 1:
        raise ValueError('Multiple matches for a key {}'.format(parameter_key))

    data = matched_lines[0].split(':')[-1].strip()
    return data


def read_layers(raw_data):
    start = '# Start of pattern'
    end = '# End of pattern'
    layers = []
    print_paths = []
    is_reading_on = False
    for line in raw_data.split('\n'):
        if line == start:
            is_reading_on = True
        elif line == end:
            is_reading_on = False
            layer = Layer(print_paths)
            layers.append(layer)
            print_paths = []
        elif is_reading_on:
            print_paths.append(PrintPath(line))

    return layers
