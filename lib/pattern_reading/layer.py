import numpy as np
from lib.pattern_reading.print_path import PrintPath
from typing import List


class Layer:
    def __init__(self, print_paths: List[PrintPath]):
        self.print_paths = print_paths
        self.path_count = len(print_paths)
        self.bounds = self.__get_bounds()
        self.centre = self.__get_centre()
        self.printing_distance = self.__get_printing_distance()
        self.non_printing_distance = self.__get_non_printing_distance()

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

    def __update_properties(self):
        self.bounds = self.__get_bounds()
        self.centre = self.__get_centre()
        self.printing_distance = self.__get_printing_distance()
        self.non_printing_distance = self.__get_non_printing_distance()

    def scale(self, ratio: float):
        for path in self.print_paths:
            path.scale(ratio)
        self.__update_properties()

    def __get_printing_distance(self):
        printing_distance = 0
        for path in self.print_paths:
            printing_distance += path.length
        return printing_distance

    def __get_non_printing_distance(self):
        if self.path_count == 1:
            return 0
        starts = np.array(list(map(lambda path: path.start(), self.print_paths)))
        ends = np.array(list(map(lambda path: path.end(), self.print_paths)))

        segments = ends[:-1] - starts[1:]
        segments_length = np.linalg.norm(segments, axis=1)
        return np.sum(segments_length)

    def move(self, offset):
        for path in self.print_paths:
            path.move(offset)
        self.__update_properties()

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
        self.__update_properties()

