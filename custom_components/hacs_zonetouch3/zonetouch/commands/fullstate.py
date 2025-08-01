"""ZoneTouch 3 fullstate class."""

import struct

import modbus_crc

from ..const import PROTOCOL_HEAD_E, PROTOCOL_HEAD_S
from ..enums import Address, Command, ExData
from .command import CommandPacket


class FullState(CommandPacket):
    """FullState class."""

    def __init__(self) -> None:
        """Init FullState."""
        super().__init__()
        self.addr_dest = Address.ADDRESS_CONSOLE
        self.addr_src = Address.ADDRESS_REMOTE
        self.command = Command.COMMAND_EXPAND

    def build_packet(self) -> bytes:
        """Build command packet."""
        header = struct.pack(
            ">BBBB",
            PROTOCOL_HEAD_S,
            PROTOCOL_HEAD_S,
            PROTOCOL_HEAD_S,
            PROTOCOL_HEAD_E,
        )

        data = struct.pack(
            ">BBB", self.addr_dest.value, self.addr_src.value, self.message_id
        )
        data += struct.pack(">B", self.command.value)
        data += struct.pack(">H", 2)
        data += struct.pack(">H", ExData.EX_DATA_FULL_STATE.value)

        crc = modbus_crc.crc16(data)

        return header + data + struct.pack("<BB", crc[1], crc[0])
