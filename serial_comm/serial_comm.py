import logging
from enum import Enum

import serial
from serial.tools import list_ports

logging.basicConfig(level=logging.DEBUG)


class Command(str, Enum):
    BYPASS_ON = "STB1"
    BYPASS_OFF = "STB0"
    FILTER_STEP_UP = "ST-"  # To *increase* the filter frequency actually *decrease* the stepper motor step count
    FILTER_STEP_DOWN = "ST+"  # To *decrease* the filter frequency actually *increase* the stepper motor step count
    FILTER_STEP_RESET = "STr"
    MODE_TX_ON = "STT"
    MODE_TX_OFF = "STR"
    GET_STATUS = "ST?"


class BadSerialResponseException(Exception):
    pass


class InternalGroundStationError(Exception):
    pass


class SerialManager:
    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self._port = port
        self._baudrate = baudrate
        self._connection = None

    def _open_serial(self) -> None:
        """Lazy initializer of serial connection."""
        if self._connection is None:
            self._connection = serial.Serial(self._port, self._baudrate, timeout=3)
        if not self._connection.is_open:
            self._connection.open()

    def _send_command(self, command: Command, parameter: str = "") -> None:
        self._open_serial()
        command_string = command.value + parameter + "\n"
        logging.debug("SEND: %s to %s", command_string[:-1], self._port)
        self._connection.write(command_string.encode("UTF-8"))
        self._connection.flush()

    def _readln_from_serial(self) -> str:
        message = self._connection.readline().decode("UTF-8").replace("\r\n", "")
        logging.debug("RECEIVED: %s from %s", message, self._port)
        return message

    def _readln_from_serial_if_in_waiting(self) -> str:
        message = ""
        if self._connection.in_waiting:
            message = self._readln_from_serial()
        return message

    @staticmethod
    def get_com_ports() -> list[str]:
        """Return list of available com (serial) ports

        Returns:
            list[str]: absolute paths of com (serial) ports available on host
        """
        return [port.device for port in list_ports.comports()]


class SerialCommander:
    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self.__serial_manager = SerialManager(port, baudrate)

    def set_bypass_on(self) -> None:
        self.__serial_manager._send_command(Command.BYPASS_ON)

    def set_bypass_off(self) -> None:
        self.__serial_manager._send_command(Command.BYPASS_OFF)

    def filter_step_up_1(self) -> None:
        self.__serial_manager._send_command(Command.FILTER_STEP_UP, "1")

    def filter_step_up_10(self) -> None:
        self.__serial_manager._send_command(Command.FILTER_STEP_UP, "10")

    def filter_step_down_1(self) -> None:
        self.__serial_manager._send_command(Command.FILTER_STEP_DOWN, "1")

    def filter_step_down_10(self) -> None:
        self.__serial_manager._send_command(Command.FILTER_STEP_DOWN, "10")

    def reset_filter(self) -> None:
        self.__serial_manager._send_command(Command.FILTER_STEP_RESET)

    def set_mode_tx_on(self) -> None:
        self.__serial_manager._send_command(Command.MODE_TX_ON)

    def set_mode_tx_off(self) -> None:
        self.__serial_manager._send_command(Command.MODE_TX_OFF)

    def get_status(self) -> str:
        self.__serial_manager._send_command(Command.GET_STATUS)
        response = self.__serial_manager._readln_from_serial()
        if not response.startswith("STST"):
            logging.error("Bad message received for get_status request")
            raise BadSerialResponseException("Bad response for get_status request")
        return response

    def check_for_error(self) -> None:
        message = self.__serial_manager._readln_from_serial_if_in_waiting()
        if message.startswith("ERROR"):
            logging.error(message)
            raise InternalGroundStationError(message)
