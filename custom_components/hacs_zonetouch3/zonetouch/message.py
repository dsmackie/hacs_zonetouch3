"""ZoneTouch 3 messages class."""

import logging
import struct

import modbus_crc

from .enums import Address, MessageType, Response
from .group import ZoneTouch3Group

_LOGGER = logging.getLogger(__name__)


class ZoneTouchMessage:
    """ZoneTouch message class."""

    def __init__(self, data: bytes | None = None) -> None:
        """Init the class."""
        self.valid = False
        self.header = None
        self.addrDest = None
        self.addrSrc = None
        self.message_id: int = 0
        self.message_type: MessageType
        self.sub_message_type: Response
        self.length = None
        self.message_data = b""
        self.temperature: float = 0
        self.groups: dict[int, ZoneTouch3Group] = {}

        if data is None:
            return

        self.data = data
        if self.__validate():
            self.__unpack_header()

            match self.message_type:
                case MessageType.MESSAGE_TYPE_SUBCOMMAND:
                    (sub_message_type,) = struct.unpack_from(">B", self.data, 10)
                    self.sub_message_type = Response(sub_message_type)
                    (_, length, count) = struct.unpack_from(">HHH", self.data, 12)
                    self.message_data = self.data[18:-2]

                    match self.sub_message_type:
                        case Response.RESPONSE_GROUP_CONTROL:
                            _LOGGER.debug("RESPONSE_GROUP_CONTROL")
                            groups = ZoneTouch3Group.parse_group_control(
                                self.message_data, count, length
                            )
                            self.groups = groups
                        case Response.RESPONSE_GROUP_NAME:
                            _LOGGER.debug("RESPONSE_GROUP_NAME")
                            group_names = ZoneTouch3Group.parse_group_names(
                                self.message_data, count, length
                            )
                            for group_index, group_name in group_names.items():
                                self.groups[group_index].name = group_name
                        case Response.RESPONSE_FAVOURITE:
                            _LOGGER.debug("RESPONSE_FAVOURITE")
                        case Response.RESPONSE_PROGRAM:
                            _LOGGER.debug("RESPONSE_PROGRAM")
                        case Response.RESPONSE_ZONE_INFO:
                            _LOGGER.debug("RESPONSE_ZONE_INFO")
                        case Response.RESPONSE_GROUPING:
                            _LOGGER.debug("RESPONSE_GROUPING")
                        case Response.RESPONSE_SERVICE:
                            _LOGGER.debug("RESPONSE_SERVICE")
                        case Response.RESPONSE_PASSWORD:
                            _LOGGER.debug("RESPONSE_PASSWORD")
                        case Response.RESPONSE_NOTIFICATION:
                            _LOGGER.debug("RESPONSE_NOTIFICATION")
                        case Response.RESPONSE_SENSOR:
                            _LOGGER.debug("RESPONSE_SENSOR")
                            self.__unpack_sensor(count, length)
                        case Response.RESPONSE_PREFERENCE:
                            _LOGGER.debug("RESPONSE_PREFERENCE")
                        case Response.RESPONSE_PARAMETERS:
                            _LOGGER.debug("RESPONSE_PARAMETERS")
                        case _:
                            _LOGGER.debug("RESPONSE_UNKNOWN")
                case _:
                    self.message_data = self.data[11:-2]

        _LOGGER.debug(Address(self.addrDest))
        _LOGGER.debug(Address(self.addrSrc))
        _LOGGER.debug(self.message_type)
        _LOGGER.debug(self.sub_message_type)
        _LOGGER.debug(self.data.hex())
        _LOGGER.debug(self.message_data.hex())

    def __validate(self) -> bool:
        """Validate received data.

        Each packet received from the controller contains a modbus checksum as the last 2 bytes.
        The data is hashed and the checksum validated against the expected checksum.
        """
        data_msg = self.data[4:-2]
        crc_orig = self.data[-2:]
        crc_check = modbus_crc.crc16(data_msg)

        self.valid = crc_orig[0] == crc_check[1] and crc_orig[1] == crc_check[0]
        return self.valid

    def __unpack_header(self) -> None:
        """Process received data header.

        Each packet has a header that defines what command the packet contains.
        We process the header so we know how to handle the received command.
        """
        (
            self.header,
            self.addrDest,
            self.addrSrc,
            self.message_id,
            message_type,
            self.length,
        ) = struct.unpack(">IBBBBH", self.data[:10])
        self.message_type = MessageType(message_type)

    def __unpack_sensor(self, count, length) -> None:
        """Process received temperature sensor data."""
        for x in range(count):
            (addr, _, temperature) = struct.unpack_from(
                ">BBH", self.data, 18 + (length * x)
            )
            if addr == 159 and temperature >= 0:
                self.temperature = (temperature - 500) / 10
