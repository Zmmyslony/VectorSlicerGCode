from pathlib import Path
from lib.pattern_reading.raw_data_handling import read_pattern, find_key_data, read_layers
import numpy as np


class Pattern:
    def __init__(self, pattern_path: Path):
        self.pattern_path = pattern_path
        raw_content, overlap_content = read_pattern(pattern_path)
        self.pixel_path_width = int(find_key_data(raw_content, "Print diameter"))
        self.pattern_name = find_key_data(raw_content, "Source directory")
        self.layers = read_layers(raw_content, overlap_content)
        self.layer_count = len(self.layers)
        self.bounds = self.__get_bounds()
        self.centre = self.__get_centre()

    def __get_bounds(self):
        layer_bounds = np.empty([self.layer_count, 4], dtype=np.float32)
        for i, layer in enumerate(self.layers):
            layer_bounds[i] = layer.bounds

        return np.array([
            np.min(layer_bounds[:, 0]),
            np.min(layer_bounds[:, 1]),
            np.max(layer_bounds[:, 2]),
            np.max(layer_bounds[:, 3])
        ])

    def __get_centre(self):
        return np.array([self.bounds[0] + self.bounds[2], self.bounds[1] + self.bounds[3]]) / 2

    def __update_bounds(self):
        self.bounds = self.__get_bounds()
        self.centre = self.__get_centre()

    def scale(self, ratio):
        """
        Scales the pattern in-place by a given ratio. Use only to go from pixel-based representation to physical
        length representation, or otherwise the slicing quality will be affected.
        :param ratio:
        :return:
        """
        for layer in self.layers:
            layer.scale(ratio)
        self.__update_bounds()

    def move(self, offset):
        """
        Moves the pattern in-place. Warning: if it is used outside of a BasePrinter.slice_pattern, it must be
        specified in pixel-based coordinates.
        :param offset: [x, y] array.
        :return:
        """
        for layers in self.layers:
            layers.move(offset)
        self.__update_bounds()

    def rotate(self, angle, centre=None):
        """
        Rotates the pattern in-place, by a given angle with the provided centre of rotation.
        :param angle:
        :param centre: If None, then the centre of the pattern will be used.
        :return:
        """
        if centre is None:
            centre = self.centre

        for layer in self.layers:
            layer.rotate(angle, centre)
        self.__update_bounds()
