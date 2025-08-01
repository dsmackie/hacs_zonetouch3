"""ZoneTouch 3 messages class."""

from ..enums import Address, Command


class CommandPacket:
    """CommandPacket class."""

    _message_id: int = 0

    def __init__(self) -> None:
        """Init CommandPacket class."""
        self.message_id = self.next_msg_id()
        self.addr_dest: Address
        self.addr_src: Address
        self.command: Command

    @classmethod
    def next_msg_id(cls) -> int:
        """Generate new message ID."""
        cls._message_id += 1
        return cls._message_id
