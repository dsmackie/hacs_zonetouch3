"""ZoneTouch 3 fullstate class."""

import logging
import struct

import modbus_crc

from ..enums import Address, Command, ExData
from .command import CommandPacket

_LOGGER = logging.getLogger(__name__)


class FullState(CommandPacket):
    """FullState class."""

    def __init__(self) -> None:
        """Init FullState."""
        super().__init__()
        self.addr_dest = Address.ADDRESS_CONSOLE
        self.command = Command.COMMAND_EXPAND

    def build_packet(self) -> bytes:
        """Build command packet."""
        data = struct.pack(
            ">BBB",
            self.addr_dest.value,
            self.addr_src.value,
            CommandPacket.next_msg_id(),
        )
        data += struct.pack(">B", self.command.value)
        data += struct.pack(">H", 2)
        data += struct.pack(">H", ExData.EX_DATA_FULL_STATE.value)

        crc = modbus_crc.crc16(data)

        return self.build_header() + data + struct.pack("<BB", crc[1], crc[0])
