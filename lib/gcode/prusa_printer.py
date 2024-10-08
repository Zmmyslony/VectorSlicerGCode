from lib.gcode.base_printer import BasePrinter, ExtrusionTypes
import numpy as np


class PrusaPrinter(BasePrinter):
    def __init__(self, print_speed=2400, non_print_speed=18000, print_width=0.8, layer_thickness=0.2,
                 lift_off_distance=5, lift_off_height=0.8, filament_diameter=1.75):
        BasePrinter.__init__(self, print_speed, non_print_speed, print_width, layer_thickness,
                             lift_off_distance=lift_off_distance, lift_off_height=lift_off_height,
                             filament_diameter=filament_diameter, extrusion_control_type=ExtrusionTypes["RelativeVariableWidth"],
                             retraction_rate=1500, retraction_length=1)
