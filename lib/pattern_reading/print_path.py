import numpy as np


class PrintPath:
    def __init__(self, string):
        current_line = np.fromstring(string, sep=',', dtype=np.float32)
        self.path_coordinates = current_line.reshape([int(current_line.shape[0] / 2), 2])
        self.position_count = self.path_coordinates.shape[0]
        self.bounds = self.__get_bounds()
        self.length = self.__get_length()

    def __get_bounds(self):
        min = np.min(self.path_coordinates, axis=0)
        max = np.max(self.path_coordinates, axis=0)
        return np.array([min[0], min[1], max[0], max[1]])

    def __get_length(self):
        segments = np.diff(self.path_coordinates, axis=0)
        segments_length = np.linalg.norm(segments, axis=1)
        return np.sum(segments_length)

    def scale(self, ratio):
        if ratio <= 0:
            raise ValueError("Scale must be positive.")

        self.path_coordinates *= ratio
        self.bounds *= ratio
        self.length *= ratio

    def move(self, offset):
        offset = np.array(offset)
        if offset.shape != (2,):
            raise ValueError("Move must be a 2-dimensional position.")
        self.path_coordinates += offset
        self.bounds += np.concatenate([offset, offset])

    def invert(self):
        self.path_coordinates = np.flip(self.path_coordinates, axis=0)

    def rotate(self, angle:float, centre=None):
        if centre is None:
            centre = np.array([0, 0], dtype=np.float32)
        else:
            centre = np.array(centre)
        if centre.shape != (2,):
            raise ValueError("Rotation centre must be a 2-dimensional position.")

        self.path_coordinates -= centre
        x = self.path_coordinates[:, 0]
        y = self.path_coordinates[:, 1]
        self.path_coordinates = np.array([np.cos(angle) * x - np.sin(angle) * y, np.sin(angle) * x + np.cos(angle) * y]).transpose()
        self.path_coordinates += centre
        self.bounds = self.__get_bounds()

    def start(self):
        return self.path_coordinates[0]

    def end(self):
        return self.path_coordinates[-1]
