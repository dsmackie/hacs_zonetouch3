"""Group file."""

from enum import Enum
import struct
from typing import Self

import modbus_crc

from .const import PROTOCOL_HEAD_E, PROTOCOL_HEAD_S
from .enums import Address, Command


class GroupPowerStatus(Enum):
    """Group Power Status."""

    NO_ZONE = -1
    ON = 1
    OFF = 0
    TURBO = 2


class ZoneTouch3Group:
    """ZoneTouch3 Group class."""

    def __init__(
        self,
        id: int,
        name: str,
        position: int,
        status: GroupPowerStatus,
        is_support_turbo: bool,
        is_spill_on: bool,
    ) -> None:
        """Init the object."""
        self.id = id
        self.name = name
        self.position = position
        self.status = status
        self.is_support_turbo = is_support_turbo
        self.is_spill_on = is_spill_on

    def getPacketSetClosed(self, closed) -> bytes:
        """Generate a packet to close the valve."""
        valve = 0
        if closed:
            valve = 2
        else:
            valve = 3
        header = struct.pack(
            ">BBBB",
            PROTOCOL_HEAD_S,
            PROTOCOL_HEAD_S,
            PROTOCOL_HEAD_S,
            PROTOCOL_HEAD_E,
        )

        data = struct.pack(
            ">BBB", Address.ADDRESS_MAIN_BOARD.value, Address.ADDRESS_REMOTE.value, 1
        )
        data += struct.pack(">B", Command.COMMAND_GROUP_CONTROL.value >> 8)
        data += struct.pack(">BBB", 0, 12, Command.COMMAND_GROUP_CONTROL.value % 256)
        data += struct.pack(">BHHHBBBB", 0, 0, 4, 1, self.id, valve, 0, 0)

        crc = modbus_crc.crc16(data)

        return header + data + struct.pack("<BB", crc[1], crc[0])

    def getPacketSetPosition(self, position) -> bytes:
        """Generate a packet to set the valve to desired position."""
        header = struct.pack(
            ">BBBB",
            PROTOCOL_HEAD_S,
            PROTOCOL_HEAD_S,
            PROTOCOL_HEAD_S,
            PROTOCOL_HEAD_E,
        )

        data = struct.pack(
            ">BBB", Address.ADDRESS_MAIN_BOARD.value, Address.ADDRESS_REMOTE.value, 1
        )
        data += struct.pack(">B", Command.COMMAND_GROUP_CONTROL.value >> 8)
        data += struct.pack(">BBB", 0, 12, Command.COMMAND_GROUP_CONTROL.value % 256)
        data += struct.pack(">BHHHBBBB", 0, 0, 4, 1, self.id, 0x80, position, 0)

        crc = modbus_crc.crc16(data)

        return header + data + struct.pack("<BB", crc[1], crc[0])

    def __eq__(self, other):
        """Check if equal with another object."""
        return (
            self.id == other.id
            and self.name == other.name
            and self.position == other.position
            and self.status == other.status
            and self.is_support_turbo == other.is_support_turbo
            and self.is_spill_on == other.is_spill_on
        )

    def __repr__(self):
        """Return a string representation of the object."""
        return f"Group(id={self.id}, name={self.name}, position={self.position}, status={self.status}, isSupportTurbo={self.is_support_turbo}, isSpillOn={self.is_spill_on})"

    @classmethod
    def parse_group_names(cls, data: bytes, count: int, length: int) -> dict[int, str]:
        """Parse group names."""
        group_names: dict[int, str] = {}
        name_len: int = struct.unpack_from(">B", data)[0]
        for x in range(count):
            (groupIndex, name) = struct.unpack_from(
                f">B{name_len}s", data, (length * x) + 2
            )
            name = name.decode("utf-8").rstrip("\x00").strip()
            group_names[groupIndex] = name
        return group_names

    @classmethod
    def parse_group_control(
        cls, data: bytes, count: int, length: int
    ) -> dict[int, Self]:
        """Parse groups."""
        groups: dict[int, Self] = {}
        data_len = 8
        for idx in range(count):
            index: int = struct.unpack_from(">B", data, (data_len * idx) + 0)[0]
            position = struct.unpack_from(">B", data, (data_len * idx) + 1)[0]
            sign = struct.unpack_from(">B", data, (data_len * idx) + 6)[0]

            groupIndex = index & 0x3F
            powerStatus = GroupPowerStatus(index >> 6)
            is_support_turbo = (sign & 0x80) != 0
            is_spill_on = (sign & 0x02) != 0

            groups[groupIndex] = cls(
                groupIndex,
                "",
                position,
                powerStatus,
                is_support_turbo,
                is_spill_on,
            )

        return groups
