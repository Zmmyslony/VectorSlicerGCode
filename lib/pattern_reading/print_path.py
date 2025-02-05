#  Copyright (c) 2025, Michał Zmyślony, mlz22@cam.ac.uk.
#
#  Please cite following publication if you use any part of this code in work you publish or distribute:
#  [1] Michał Zmyślony M., Klaudia Dradrach, John S. Biggins,
#     Slicing vector fields into tool paths for additive manufacturing of nematic elastomers,
#     Additive Manufacturing, Volume 97, 2025, 104604, ISSN 2214-8604, https://doi.org/10.1016/j.addma.2024.104604.
#
#  This file is part of VectorSlicerGCode.
#
#  VectorSlicerGCode is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
#  License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  VectorSlicerGCode is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
#  implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
#  Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with VectorSlicerGCode.
#  If not, see <https://www.gnu.org/licenses/>.

import numpy as np


class PrintPath:
    def __init__(self, string, overlap=None):
        current_line = np.fromstring(string, sep=',', dtype=np.float32)
        self.path_coordinates = current_line.reshape([int(current_line.shape[0] / 2), 2])
        self.position_count = self.path_coordinates.shape[0]
        self.overlap = np.fromstring(overlap, sep=',', dtype=np.float32) if overlap is not None else np.zeros(
            self.position_count)
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

    def rotate(self, angle: float, centre=None):
        if centre is None:
            centre = np.array([0, 0], dtype=np.float32)
        else:
            centre = np.array(centre)
        if centre.shape != (2,):
            raise ValueError("Rotation centre must be a 2-dimensional position.")

        self.path_coordinates -= centre
        x = self.path_coordinates[:, 0]
        y = self.path_coordinates[:, 1]
        self.path_coordinates = np.array(
            [np.cos(angle) * x - np.sin(angle) * y, np.sin(angle) * x + np.cos(angle) * y]).transpose()
        self.path_coordinates += centre
        self.bounds = self.__get_bounds()

    def start(self):
        return self.path_coordinates[0]

    def end(self):
        return self.path_coordinates[-1]
