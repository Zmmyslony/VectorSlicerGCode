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

from pathlib import Path
from lib.pattern_reading.raw_data_handling import read_pattern, find_key_data, read_layers
import numpy as np


class Pattern:
    def __init__(self, pattern_name: str):
        """
        :param pattern_name:  Name of the pattern as a string: it will search for the pattern with this name in the slicer's output directory.
        """
        # self.pattern_path = pattern_name
        raw_content, overlap_content = read_pattern(pattern_name)
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

    def scale(self, ratio: float):
        """
        Scales the pattern in-place by a given ratio. Use only to go from pixel-based representation to physical
        length representation, or otherwise the slicing quality will be affected.
        :param ratio:
        :return:
        """
        for layer in self.layers:
            layer.scale(ratio)
        self.__update_bounds()

    def move(self, offset: np.ndarray):
        """
        Moves the pattern in-place. Warning: it must be specified in pixel-based coordinates, as translation from
        pixels to physical units happens when the pattern is sliced.
        :param offset: [x, y] array.
        :return:
        """
        for layers in self.layers:
            layers.move(offset)
        self.__update_bounds()

    def rotate(self, angle: float, centre: np.ndarray = None):
        """
        Rotates the pattern in-place, by a given angle with the provided centre of rotation.
        :param angle: [rad]
        :param centre: If None, then the centre of the pattern will be used.
        :return:
        """
        if centre is None:
            centre = self.centre

        for layer in self.layers:
            layer.rotate(angle, centre)
        self.__update_bounds()
