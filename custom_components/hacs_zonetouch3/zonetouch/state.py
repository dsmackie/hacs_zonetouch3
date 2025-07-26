"""FullState class."""

from __future__ import annotations

from enum import Enum
import logging
import struct

from .enums import Response
from .group import GroupPowerStatus, ZoneTouch3Group
from .message import ZoneTouchMessage

_LOGGER = logging.getLogger(__name__)


class ServiceDueStatus(Enum):
    """Group Power Status."""

    UNKNOWN = -1
    NO = 0
    HALF_YEAR = 1
    ONE_YEAR = 2
    TWO_YEARS = 3


class ZoneTouch3State:
    """A class to hold FullState."""

    def __init__(self) -> None:
        """Init state."""
        self.device_id: int = 0
        self.owner: str = None
        self.opt: int = 0
        self.service_due: ServiceDueStatus = ServiceDueStatus.UNKNOWN
        self.password: str = None
        self.installer: str = None
        self.telephone: str = None
        self.temperature: float = 0
        self.hardware_version: str = None
        self.firmware_version: str = None
        self.boot_version: str = None
        self.console_version: str = None
        self.console_id: str = None
        self.groups: dict[int, ZoneTouch3Group] = {}

    @staticmethod
    def from_bytes(raw_response: bytes) -> ZoneTouch3State:
        """Create state from raw response."""
        zonetouch = ZoneTouch3State()
        header, address, message_id, message_type, data_length = struct.unpack(
            ">IHBBH", raw_response[:10]
        )
        data_raw = raw_response[-data_length - 2 : -2]
        # crc16_check = data[-data_length-2:-2]

        if message_type == 31:
            data_type = struct.unpack_from(">H", data_raw, 0)[0]
            if data_type == 65520:
                len = zonetouch.__parseSystemInfo(data_raw)
                zonetouch.__parseGroupInfo(data_raw[len:])

        return zonetouch

    def updateFromMessage(self, msg: ZoneTouchMessage) -> None:
        """Update state from new message."""
        match msg.sub_message_type:
            case Response.RESPONSE_SENSOR:
                self.temperature = msg.temperature
            case Response.RESPONSE_GROUP_CONTROL:
                for groupIndex in msg.groups:
                    self.groups[groupIndex].position = msg.groups[groupIndex].position
                    self.groups[groupIndex].status = msg.groups[groupIndex].status
                    self.groups[groupIndex].is_spill_on = msg.groups[
                        groupIndex
                    ].is_spill_on
            case Response.RESPONSE_GROUP_NAME:
                for groupIndex, group_data in msg.groups.items():
                    if groupIndex in self.groups:
                        self.groups[groupIndex].name = group_data.name
            case _:
                _LOGGER.debug("Unhandled sub message type")

    def __parseSystemInfo(self, data_raw):
        """Parse raw data."""
        self.device_id = (
            struct.unpack_from(">8s", data_raw, 2)[0]
            .decode("utf-8")
            .rstrip("\x00")
            .strip()
        )
        self.owner = (
            struct.unpack_from(">16s", data_raw, 10)[0]
            .decode("utf-8")
            .rstrip("\x00")
            .strip()
        )
        self.opt = struct.unpack_from(">B", data_raw, 26)[0]

        # Service Due
        _service_due = struct.unpack_from(">B", data_raw, 27)[0]
        self.service_due = ServiceDueStatus(_service_due)

        self.password = struct.unpack_from(">8s", data_raw, 28)[0]
        self.installer = struct.unpack_from(">10s", data_raw, 36)[0]
        self.telephone = struct.unpack_from(">12s", data_raw, 46)[0]
        self.temperature = struct.unpack_from(">h", data_raw, 58)[0]
        self.temperature = (self.temperature - 500) / 10

        offset = 60
        _hardware_version_len = struct.unpack_from(">b", data_raw, offset)[0]
        self.hardware_version = (
            struct.unpack_from(f">{_hardware_version_len}s", data_raw, offset + 1)[0]
            .decode("utf-8")
            .rstrip("\x00")
            .strip()
        )

        offset += _hardware_version_len + 1
        _firmware_version_length = struct.unpack_from(">b", data_raw, offset)[0]
        self.firmware_version = (
            struct.unpack_from(f">{_firmware_version_length}s", data_raw, offset + 1)[0]
            .decode("utf-8")
            .rstrip("\x00")
            .strip()
        )

        offset += _firmware_version_length + 1
        _boot_version_length = struct.unpack_from(">b", data_raw, offset)[0]
        self.boot_version = struct.unpack_from(
            f">{_boot_version_length}s", data_raw, offset + 1
        )[0]

        offset += _boot_version_length + 1
        _console_version_length = struct.unpack_from(">b", data_raw, offset)[0]
        self.console_version = struct.unpack_from(
            f">{_console_version_length}s", data_raw, offset + 1
        )[0]

        offset += _console_version_length + 1
        _console_id_length = struct.unpack_from(">b", data_raw, offset)[0]
        self.console_id = struct.unpack_from(
            f">{_console_id_length}s", data_raw, offset + 1
        )[0]

        return offset + _console_id_length + 1

    def __parseOneGroupInfo(self, data) -> ZoneTouch3Group:
        index: int = struct.unpack_from(">B", data, 0)[0]
        position = struct.unpack_from(">B", data, 1)[0]
        sign = struct.unpack_from(">B", data, 6)[0]

        groupIndex = index & 0x3F
        powerStatus = GroupPowerStatus(index >> 6)
        is_support_turbo = (sign & 0x80) != 0
        is_spill_on = (sign & 0x02) != 0

        return ZoneTouch3Group(
            groupIndex,
            "name",
            position,
            powerStatus,
            is_support_turbo,
            is_spill_on,
        )

    def __parseGroupInfo(self, data):
        """Parse group info."""
        group_count = struct.unpack_from(">b", data, 0)[0]
        data_len = struct.unpack_from(">b", data, 1)[0]
        name_len = struct.unpack_from(">b", data, 2)[0]

        for idx, x in enumerate(range(group_count)):
            group = self.__parseOneGroupInfo(
                data[data_len * idx + 4 : (data_len * idx) + 12]
            )
            group.name = (
                struct.unpack_from(f">{name_len}s", data, (data_len * idx) + 14)[0]
                .decode("utf-8")
                .rstrip("\x00")
                .strip()
            )

            self.groups[group.id] = group

    def __str__(self):
        """Build str of object."""
        return f"""
        Device ID:\t{self.device_id}
        Owner:\t{self.owner}`
        Temperature:\t{self.temperature}
        Groups:\t{self.groups}
        """
