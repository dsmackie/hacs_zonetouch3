import logging
import struct

import modbus_crc

from .enums import Address, MessageType, Response
from .group import GroupPowerStatus, ZoneTouch3Group

_LOGGER = logging.getLogger(__name__)


class ZoneTouchMessage:
    """ZoneTouch message class."""

    def __init__(self, data: bytes | None = None) -> None:
        """Init the class."""
        self.valid = False
        self.header = None
        self.addrDest = None
        self.addrSrc = None
        self.message_id = None
        self.message_type: MessageType = None
        self.sub_message_type: Response = None
        self.length = None
        self.message_data = None
        self.temperature: float = 0
        self.groups: dict[int, ZoneTouch3Group] = {}

        if data is None:
            return

        self.data = data
        if self.__validate():
            self.__unpack()

        _LOGGER.debug(Address(self.addrDest))
        _LOGGER.debug(Address(self.addrSrc))
        _LOGGER.debug(self.message_type)
        _LOGGER.debug(self.sub_message_type)
        _LOGGER.debug(self.data.hex())
        _LOGGER.debug(self.message_data.hex())

        match self.sub_message_type:
            case Response.RESPONSE_GROUP_CONTROL:
                _LOGGER.debug("RESPONSE_GROUP_CONTROL")
            case Response.RESPONSE_GROUP_NAME:
                _LOGGER.debug("RESPONSE_GROUP_NAME")
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
            case Response.RESPONSE_PREFERENCE:
                _LOGGER.debug("RESPONSE_PREFERENCE")
            case Response.RESPONSE_PARAMETERS:
                _LOGGER.debug("RESPONSE_PARAMETERS")
            case _:
                _LOGGER.debug("RESPONSE_UNKNOWN")

    def __validate(self) -> bool:
        data_msg = self.data[4:-2]
        crc_orig = self.data[-2:]
        crc_check = modbus_crc.crc16(data_msg)

        self.valid = crc_orig[0] == crc_check[1] and crc_orig[1] == crc_check[0]
        return self.valid

    def __unpack(self) -> None:
        """Unpack message into each component."""
        (
            self.header,
            self.addrDest,
            self.addrSrc,
            self.message_id,
            message_type,
            self.length,
        ) = struct.unpack(">IBBBBH", self.data[:10])
        self.message_type = MessageType(message_type)

        match self.message_type:
            case MessageType.MESSAGE_TYPE_SUBCOMMAND:
                (sub_message_type,) = struct.unpack_from(">B", self.data, 10)
                self.sub_message_type = Response(sub_message_type)
                self.message_data = self.data[12:-2]
                (_, length, count) = struct.unpack_from(">HHH", self.data, 12)
                match self.sub_message_type:
                    case Response.RESPONSE_SENSOR:
                        for x in range(count):
                            (addr, _, temperature) = struct.unpack_from(
                                ">BBH", self.data, 18 + (length * x)
                            )
                            if addr == 159 and temperature >= 0:
                                self.temperature = (temperature - 500) / 10
                    case Response.RESPONSE_GROUP_CONTROL:
                        self.__parseGroupControl(self.data[18:], count)

            case _:
                self.message_data = self.data[11:-2]

    def __parseGroupControl(self, data, count) -> None:
        for idx in range(count):
            data_len = 8
            index: int = struct.unpack_from(">B", data, (data_len * idx) + 0)[0]
            position = struct.unpack_from(">B", data, (data_len * idx) + 1)[0]
            sign = struct.unpack_from(">B", data, (data_len * idx) + 2)[0]

            groupIndex = index & 0x3F
            powerStatus = GroupPowerStatus(index >> 6)
            is_support_turbo = sign & 0x80 != 0
            is_spill_on = sign & 0x02 != 0

            group = ZoneTouch3Group(
                groupIndex,
                None,
                position,
                powerStatus,
                is_support_turbo,
                is_spill_on,
            )

            self.groups[groupIndex] = group
