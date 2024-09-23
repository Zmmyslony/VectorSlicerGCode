import numpy as np
from lib.pattern_reading.print_path import PrintPath
from typing import List


class Layer:
    def __init__(self, print_paths: List[PrintPath]):
        self.print_paths = print_paths
        self.path_count = len(print_paths)
        self.bounds = self.__get_bounds()
        self.centre = self.__get_centre()

    def __get_bounds(self):
        path_bounds = np.empty([self.path_count, 4], dtype=np.float32)
        for i, path in enumerate(self.print_paths):
            path_bounds[i] = path.bounds

        return np.array([
            np.min(path_bounds[:, 0]),
            np.min(path_bounds[:, 1]),
            np.max(path_bounds[:, 2]),
            np.max(path_bounds[:, 3])
        ])

    def __get_centre(self):
        return np.array([self.bounds[0] + self.bounds[2], self.bounds[1] + self.bounds[3]]) / 2

    def __update_bounds(self):
        self.bounds = self.__get_bounds()
        self.centre = self.__get_centre()

    def __scale(self, ratio: float):
        for path in self.print_paths:
            path.__scale(ratio)
        self.__update_bounds()

    def move(self, offset):
        for path in self.print_paths:
            path.move(offset)
        self.__update_bounds()

    def invert(self):
        """
        Inverts the order of the printed lines, i.e. flips end with the beginning.
        :return:
        """
        self.print_paths.reverse()
        for path in self.print_paths:
            path.invert()

    def rotate(self, angle, centre=None):
        if centre is None:
            centre = self.centre

        for path in self.print_paths:
            path.rotate(angle, centre)
        self.__update_bounds()