"""ZoneTouch 3 group class."""

import struct

import modbus_crc

from ..enums import Address, Command
from .command import CommandPacket


class GroupCommand(CommandPacket):
    """FullState class."""

    def __init__(self) -> None:
        """Init FullState."""
        super().__init__()
        self.addr_dest = Address.ADDRESS_MAIN_BOARD
        self.command = Command.COMMAND_GROUP_CONTROL

    def build_position_packet(self, group_id: int, position: int) -> bytes:
        """Generate a packet to set the group to desired position."""
        data = struct.pack(
            ">BBB", self.addr_dest.value, self.addr_src.value, self.message_id
        )
        data += struct.pack(">B", self.command.value >> 8)
        data += struct.pack(">BBB", 0, 12, self.command.value % 256)
        data += struct.pack(">BHHHBBBB", 0, 0, 4, 1, group_id, 0x80, position, 0)

        crc = modbus_crc.crc16(data)

        return self.build_header() + data + struct.pack("<BB", crc[1], crc[0])

    def build_closed_packet(self, group_id: int, closed: bool) -> bytes:
        """Generate a packet to close the valve."""
        valve = 0
        if closed:
            valve = 2
        else:
            valve = 3

        data = struct.pack(
            ">BBB", self.addr_dest.value, self.addr_src.value, self.message_id
        )
        data += struct.pack(">B", self.command.value >> 8)
        data += struct.pack(">BBB", 0, 12, self.command.value % 256)
        data += struct.pack(">BHHHBBBB", 0, 0, 4, 1, group_id, valve, 0, 0)

        crc = modbus_crc.crc16(data)

        return self.build_header() + data + struct.pack("<BB", crc[1], crc[0])
