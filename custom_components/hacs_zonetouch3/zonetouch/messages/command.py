"""ZoneTouch 3 messages class."""

import struct

import modbus_crc

from ..enums import Address, Command, MessageType, Protocol, Response


class CommandPacket:
    """CommandPacket class."""

    _message_id: int = 0

    def __init__(self) -> None:
        """Init CommandPacket class."""
        self.addr_dest: Address
        self.addr_src: Address = Address.ADDRESS_REMOTE
        self.command: Command
        self.raw_message: bytes
        self.valid: bool = False
        self.message_type: MessageType
        self.sub_message_type: Response
        self.length = None
        self.message_data = b""

    @classmethod
    def next_msg_id(cls) -> int:
        """Generate new message ID."""
        cls._message_id += 1
        if cls._message_id > 255:
            cls._message_id = 1
        print(cls._message_id)
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

    def validate(self) -> bool:
        """Validate received data.

        Each packet received from the controller contains a modbus checksum as the last 2 bytes.
        The data is hashed and the checksum validated against the expected checksum.
        """
        data_msg = self.raw_message[4:-2]
        crc_orig = self.raw_message[-2:]
        crc_check = modbus_crc.crc16(data_msg)

        self.valid = crc_orig[0] == crc_check[1] and crc_orig[1] == crc_check[0]
        return self.valid

    def unpack_header(self) -> None:
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
        ) = struct.unpack(">IBBBBH", self.raw_message[:10])
        self.message_type = MessageType(message_type)
