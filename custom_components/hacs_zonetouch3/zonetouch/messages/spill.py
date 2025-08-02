"""ZoneTouch 3 spill class."""

from __future__ import annotations

import logging
import struct

import modbus_crc

from ..enums import Address, Command, ExData, Response
from .command import CommandPacket

_LOGGER = logging.getLogger(__name__)


class Spill(CommandPacket):
    """FullState class."""

    def __init__(self) -> None:
        """Init FullState."""
        super().__init__()
        self.addr_dest = Address.ADDRESS_MAIN_BOARD
        self.addr_src = Address.ADDRESS_REMOTE
        self.command = Command.COMMAND_SPILL
        self.groups: list[int] = []

    @staticmethod
    def from_bytes(raw_response: bytes) -> Spill | None:
        spill = Spill()
        spill.raw_message = raw_response
        if spill.validate():
            spill.unpack_header()
            (sub_message_type,) = struct.unpack_from(">B", spill.raw_message, 10)
            spill.sub_message_type = Response(sub_message_type)
            (_, length, count) = struct.unpack_from(">HHH", spill.raw_message, 12)
            spill.message_data = spill.raw_message[18:-2]
            spill.groups = [n for n in range(32) if (spill.message_data[2] >> n) & 1]
            return spill
        return None

    def build_packet(self) -> bytes:
        """Build command packet."""
        data = struct.pack(
            ">BBB",
            self.addr_dest.value,
            self.addr_src.value,
            CommandPacket.next_msg_id(),
        )
        data += struct.pack(">B", self.command.value >> 8)
        data += struct.pack(">H", 8)
        data += struct.pack(">B", self.command.value % 256)
        data += struct.pack(">BHHH", 0, 0, 0, 0)

        crc = modbus_crc.crc16(data)

        return self.build_header() + data + struct.pack("<BB", crc[1], crc[0])
