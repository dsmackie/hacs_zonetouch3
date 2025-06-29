"""Group file."""

from enum import Enum
import struct

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
            and self.position == other.position
            and self.status == other.status
        )

    def __repr__(self):
        """Return a string representation of the object."""
        return f"Group(id={self.id}, name={self.name}, position={self.position}, status={self.status}, isSupportTurbo={self.is_support_turbo}, isSpillOn={self.is_spill_on})"
