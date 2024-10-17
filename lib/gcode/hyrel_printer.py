import math

import numpy as np

from lib.gcode.base_printer import BasePrinter, ExtrusionTypes

KR2_15_PULSES_PER_UL = 1297


def tool_number_m_command(tool_number):
    return tool_number + 11


class HyrelPrinter(BasePrinter):
    def __init__(self, print_speed, non_print_speed, print_width, layer_thickness,
                 tool_number, priming_pulses, nozzle_temperature,
                 uv_duty_cycle, bed_temperature=0,
                 cleaning_lines=17, cleaning_length=20, first_layer_height=None,
                 pulses_per_ul=KR2_15_PULSES_PER_UL, extrusion_multiplier=1.0,
                 priming_rate=10000, unpriming_rate=None, height_offset_register=2,
                 ):
        super().__init__(print_speed, non_print_speed, print_width, layer_thickness,
                         first_layer_height=first_layer_height,
                         extrusion_control_type=ExtrusionTypes["OnOff"])

        self.tool_number = tool_number
        self.priming_pulses = priming_pulses
        self.bed_temperature = bed_temperature
        self.nozzle_temperature = nozzle_temperature
        self.uv_duty_cycle = uv_duty_cycle

        self.pulses_per_ul = pulses_per_ul
        self.extrusion_multiplier = extrusion_multiplier
        self.priming_rate = priming_rate
        self.unpriming_rate = priming_rate if unpriming_rate is None else unpriming_rate
        self.cleaning_lines = cleaning_lines
        self.cleaning_length = cleaning_length

        self.height_offset_register = height_offset_register

        self.__generate_secondary_header()

    def __set_units_to_millimetres(self):
        self._break_body()
        self._comment_body("Setting units to millimetres.")
        self._command_body("G21")

    def __configure_flow(self, path_width: float = None, layer_thickness: float = None, flow_multiplier: float = None,
                         pulses_per_ul: int = None, tool: int = None):
        if path_width is None: path_width = self._print_width
        if tool is None: tool = self.tool_number
        if layer_thickness is None: layer_thickness = self._layer_thickness
        if flow_multiplier is None: flow_multiplier = self.extrusion_multiplier
        if pulses_per_ul is None: pulses_per_ul = self.pulses_per_ul

        self._break_body()
        self._comment_body("Configuring flow.")
        self._command_body(f"M221 T{tool_number_m_command(tool):d} W{path_width:.3f} "
                           f"Z{layer_thickness:.3f} S{flow_multiplier:.3f} P{pulses_per_ul:d}")

    def __set_nozzle_temperature(self, temperature: float = None, tool_number: int = None):
        if temperature is None: temperature = self.nozzle_temperature
        if tool_number is None: tool_number = self.tool_number
        self._break_body()
        self._comment_body(f"Setting nozzle temperature to {temperature:d}C.")
        self._command_body(f"M109 T{tool_number_m_command(tool_number)} S{temperature:d}")

    def __set_bed_temperature(self, temperature: float = None):
        if temperature is None: temperature = self.bed_temperature
        self._break_body()
        self._comment_body(f"Setting bed temperature to {temperature:d}C.")
        self._command_body(f"M190 S{temperature:d}")

    def __turn_motors_off(self):
        self._break_body()
        self._comment_body("Turning motors off.")
        self._command_body("M18")

    def __signal_finished_print(self):
        self._break_body()
        self._comment_footer("Signalling finished print.")
        self._command_footer("M30")

    def __clear_offsets(self):
        self._break_body()
        self._comment_body("Clearing offsets.")
        self._command_body("G53")

    def __select_tool(self, tool_number: int):
        if not 0 <= tool_number < 4: raise ValueError("Tool number can only be in range [0, 3]")
        self.tool_number = tool_number
        self._break_body()
        self._comment_body("Selecting tool.")
        self._command_body(f"T{tool_number:d}")

    def __define_height_offset(self, height: float, register: int):
        if not 0 <= height <= 120: raise ValueError("Height offset must be in range [0, 120]")

        self._break_body()
        self._comment_footer(f"Setting height offset to register {register:d}.")
        self._command_body(f"M660 H{register:d} Z{height:.3f}")

    def __define_tool_offset(self, offset: np.ndarray, tool_number: int = None):
        if tool_number is None: tool_number = self.tool_number
        offset = np.array(offset)
        if offset.shape != (3,): raise ValueError("Tool offset must be a 3-valued vector.")
        if not 0 <= offset[0] <= 200: raise ValueError("X-offset must be in range [0, 200]")
        if not 0 <= offset[1] <= 200: raise ValueError("Y-offset must be in range [0, 200]")
        if not 0 <= offset[2] <= 120: raise ValueError("Z-offset must be in range [0, 120]")

        self._break_body()
        self._comment_body("Setting tool offset.")
        self._command_body(f"M6 T{tool_number_m_command(tool_number)} O{tool_number + 1} X{offset[0]:.3f} "
                           f"Y{offset[1]:.3f} Z{offset[2]:.3f}")

    def __configure_prime(self, pulse_rate: int, number_of_pulses: int, dwell_time: int = 0,
                          is_executed_immediately: bool = False, tool_number: int = None):
        if tool_number is None: tool_number = self.tool_number
        if not 0 <= number_of_pulses <= 65535:
            raise ValueError("Pulse count must be less than 65535 due to use of unsigned short by Hyrel.")
        self._break_body()
        self._comment_body("Configuring priming.")
        self._command_body(
            f"M722 T{tool_number_m_command(tool_number)} S{pulse_rate:d} E{number_of_pulses:d} P{dwell_time:d}")
        if is_executed_immediately:
            self._comment_body("Priming now.")
            self._command_body(f"M722 T{tool_number_m_command(tool_number)} I1")

    def __configure_unprime(self, pulse_rate: int, number_of_pulses: int, dwell_time: int,
                            is_executed_immediately: bool = False, tool_number: int = None):

        if tool_number is None: tool_number = self.tool_number
        if not 0 <= number_of_pulses <= 65535:
            raise ValueError("Pulse count must be less than 65535 due to use of unsigned short by Hyrel.")
        self._break_body()
        self._comment_body("Configuring unpriming.")
        self._command_body(
            f"M721 T{tool_number_m_command(tool_number)} S{pulse_rate:d} E{number_of_pulses:d} P{dwell_time:d}")
        if is_executed_immediately:
            self._comment_body("Unpriming now.")
            self._command_body(f"M721 T{tool_number_m_command(tool_number)} I1")

    def __disable_priming(self, tool_number: int = None):
        if tool_number is None: tool_number = self.tool_number
        self.__configure_prime(0, 0, 0, tool_number=tool_number)

    def __disable_unpriming(self, tool_number: int = None):
        if tool_number is None: tool_number = self.tool_number
        self.__configure_unprime(0, 0, 0, tool_number=tool_number)

    def __generate_secondary_header(self):
        self._break_header()
        self._comment_header("File generated for use with a Hyrel printer.")

        self._comment_header(f"Default printing tool: T{self.tool_number} (T1{self.tool_number + 1}).")
        self._comment_header(f"Path width: {self._print_width} mm.")
        self._comment_header(f"First layer height: {self._first_layer_thickness} mm.")
        self._comment_header(f"Layer thickness: {self._layer_thickness} mm.")

        self._comment_header("Ensure that your printer is compatible with the resulting gcode.")
        self._break_header()

    def generate_zig_zag_pattern(self, start_position, n_lines: int, l_lines: float, line_spacing: float,
                                 is_going_in_positive_x=True, height=None):
        self._comment_body(
            f"Generating a zig-zag pattern of total length of {n_lines * l_lines:.1f} mm ({n_lines:d} of {l_lines:.1f} mm).")

        if start_position is not None: self._non_printing_move(np.array(start_position))
        self._z_move(self._first_layer_thickness) if height is None else self._z_move(height)

        for i in range(n_lines):
            if is_going_in_positive_x:
                self._printing_move_relative([l_lines, 0])
            else:
                self._printing_move_relative([-l_lines, 0])
            self._printing_move_relative([0, line_spacing])
            is_going_in_positive_x = not is_going_in_positive_x

    def __prime_now(self, length: float, prime_pulses: int, prime_rate: int, line_spacing: float,
                    tool_number: int = None, starting_position=None, is_going_in_positive_x=True):
        """
        Due to Hyrel's implementation of priming, priming cannot use more than 65535 pulses at once, so when
        prime_pulses is greater than that, multiple lines need to be used.
        :param length:
        :param prime_rate:
        :param line_spacing:
        :param tool_number:
        :return:
        """
        if tool_number is None: tool_number = self.tool_number

        priming_lines: int = math.ceil(prime_pulses / 65535)
        priming_pulses_per_line: float = prime_pulses / priming_lines
        single_line_time: float = priming_pulses_per_line / prime_rate  # in seconds
        priming_speed: float = min(self._print_speed, 60 * length / single_line_time)

        self._break_body()
        self._comment_body("Starting initial priming.")
        self.__disable_unpriming(tool_number)
        self.__configure_prime(prime_rate, int(priming_pulses_per_line), tool_number=tool_number)
        if starting_position is None:
            self._non_printing_move([0, 0, 0])
        else:
            self._non_printing_move(starting_position)

        for i in range(priming_lines):
            if is_going_in_positive_x:
                self._printing_move_relative([length, 0], speed=priming_speed)
            else:
                self._printing_move_relative([-length, 0], speed=priming_speed)
            self._non_printing_move_relative([0, line_spacing])
            is_going_in_positive_x = not is_going_in_positive_x

        self.__disable_priming(tool_number)
        self._comment_body("Priming complete.")
        return is_going_in_positive_x, priming_lines

    def __unprime_now(self, prime_pulses: int = None, prime_rate: int = None, length: float = 10,
                      tool_number: int = None, starting_position=None):
        if tool_number is None: tool_number = self.tool_number
        if prime_pulses is None: prime_pulses = self.priming_pulses
        if prime_rate is None: prime_rate = self.unpriming_rate

        priming_lines: int = math.ceil(prime_pulses / 65535)
        priming_pulses_per_line: float = prime_pulses / priming_lines
        single_line_time: float = priming_pulses_per_line / prime_rate  # in seconds
        priming_speed: float = min(self._print_speed, 60 * length / single_line_time)

        self._comment_body("Starting unpriming.")
        self._home_2d()
        for i in range(priming_lines):
            self.__configure_unprime(prime_rate, int(priming_pulses_per_line), 0, True, tool_number)
            self._z_move_incremental(length, priming_speed)
        self.__disable_unpriming(tool_number)
        self._comment_body("Unpriming complete.")

    def _configure_offsets(self):
        self._break_body()
        self._comment_body("Invoking offsets.")
        self._non_printing_move([0, 0])
        self.__define_height_offset(self._first_layer_thickness, self.height_offset_register)

    def _clean_with_priming(self):
        is_going_in_positive_x, priming_lines = (
            self.__prime_now(self.cleaning_length, self.priming_pulses, self.priming_rate, self._print_width * 2))

        self.generate_zig_zag_pattern(None, self.cleaning_lines - priming_lines, self.cleaning_length,
                                      self._print_width * 2, is_going_in_positive_x)
        self._comment_body("Cleaning with priming complete.")

    def initial_configuration(self, tool_offset):
        self.__set_units_to_millimetres()
        self.__clear_offsets()

        self._home_2d()
        self.__define_tool_offset(tool_offset)

        self.__set_nozzle_temperature()
        self.__set_bed_temperature()

        self.__disable_priming()
        self.__disable_unpriming()

        self.__configure_flow()
        self.__select_tool(self.tool_number)

        self._clean_with_priming()
        self._configure_uv_array(self.uv_duty_cycle, self.tool_number)

        self._comment_body("Initial Hyrel configuration complete.")
        self._break_body()

    def _configure_uv_pen(self, pen_tool_number, uv_duty_cycle=None, head_tool_number=None):
        if uv_duty_cycle is None: uv_duty_cycle = self.uv_duty_cycle
        if head_tool_number is None: head_tool_number = self.tool_number

        self._break_body()
        self._comment_body(f"Linking the UV pen to switch on during printing moves of T{head_tool_number:d}")
        self._command_body(f"M703 T{tool_number_m_command(pen_tool_number)} S{tool_number_m_command(head_tool_number)}")
        self._command_body(f"M620 T{tool_number_m_command(pen_tool_number)} E1")
        self._command_body(f"M621 T{tool_number_m_command(pen_tool_number)} P{uv_duty_cycle:d}")

    def _configure_uv_array(self, uv_duty_cycle=None, head_tool_number=None):
        if uv_duty_cycle is None: uv_duty_cycle = self.uv_duty_cycle
        if head_tool_number is None: head_tool_number = self.tool_number
        if not 0 <= uv_duty_cycle <= 100: raise ValueError("UV duty cycle must be between 0 and 100.")

        self._break_body()
        self._comment_body("Setting UV array duty cycle.")
        self._command_body(f"M106 T{tool_number_m_command(head_tool_number):d} P{uv_duty_cycle:d}")

    def finish_print(self):
        self.__unprime_now()
        self.__set_bed_temperature(0)
        self.__set_nozzle_temperature(0)
        self._home_2d()
        self.__turn_motors_off()
        self.__signal_finished_print()
