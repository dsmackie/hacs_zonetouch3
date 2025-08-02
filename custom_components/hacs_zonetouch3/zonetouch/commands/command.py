"""ZoneTouch 3 messages class."""

import struct

from ..enums import Address, Command, Protocol


class CommandPacket:
    """CommandPacket class."""

    _message_id: int = 0

    def __init__(self) -> None:
        """Init CommandPacket class."""
        self.message_id = self.next_msg_id()
        self.addr_dest: Address
        self.addr_src: Address = Address.ADDRESS_REMOTE
        self.command: Command

    @classmethod
    def next_msg_id(cls) -> int:
        """Generate new message ID."""
        cls._message_id += 1
        return cls._message_id

    def build_header(self) -> bytes:
        """Generate header bytes."""
        return struct.pack(
            ">BBBB",
            Protocol.PROTOCOL_HEAD_S.value,
            Protocol.PROTOCOL_HEAD_S.value,
            Protocol.PROTOCOL_HEAD_S.value,
            Protocol.PROTOCOL_HEAD_E.value,
        )
