import asyncio
from collections.abc import Callable
import logging
import socket
import struct

import modbus_crc

from .message import ZoneTouchMessage
from .state import ZoneTouch3State

_LOGGER = logging.getLogger(__name__)

PROTOCOL_HEAD_S = 0x55
PROTOCOL_HEAD_E = 0xAA


class ZoneTouch3Exception(Exception):
    """Base class for errors throw by ZoneTouch3."""

    def __init__(self, reason: str | None = None) -> None:
        """Init the exception."""
        self.reason = reason


class ZoneTouch3ClientError(ZoneTouch3Exception):
    """Exception to indicate a general API error."""


class ZoneTouch3ConnectionFailedException(ZoneTouch3Exception):
    """Exception to indicate a general API error."""


class DataPacket:
    def __init__(self):
        pass


class ZoneTouch:
    ADDRESS_CONSOLE = 0x90
    ADDRESS_REMOTE = 0xB0
    COMMAND_EXPAND = 0x1F
    EX_DATA_FULL_STATE = 0xFFF0
    PROTOCOL_HEAD_S = 0x55
    PROTOCOL_HEAD_E = 0xAA

    def __init__(
        self,
        host: str,
        port: int,
        on_state_update: Callable | None = None,
        on_disconnect: Callable | None = None,
    ) -> None:
        """Sample API Client."""
        self._host = host
        self._port = port
        self.sock: socket.socket
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.connected = False
        self.on_state_update = on_state_update
        self.on_disconnect = on_disconnect
        self.listener: asyncio.Task
        self.state = ZoneTouch3State()

    async def async_get_full_state(self) -> ZoneTouch3State:
        """Get data from the API."""
        p = self.getPacketFetchFullState()
        data = await self.send(p, True)
        self.state = ZoneTouch3State.from_bytes(data)
        return self.state

    async def connect(self):
        """Connect to the ZoneTouch3 controller."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Enable TCP keepalive
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            # Set TCP keepalive parameters
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)

            # Disable Nagle's algorithm
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            self.sock.setblocking(False)

            await asyncio.get_event_loop().sock_connect(
                self.sock, (self._host, self._port)
            )

            conn = asyncio.open_connection(sock=self.sock)
            self.reader, self.writer = await asyncio.wait_for(conn, timeout=5)
            self.connected = True
            _LOGGER.debug("Connected to %s:%s", self._host, self._port)
        except Exception as exception:
            self.sock.close()
            raise ZoneTouch3ConnectionFailedException(
                f"Failed to connect: {exception}"
            ) from exception

    async def close(self) -> None:
        """Close the connection."""
        _LOGGER.debug("Connection closing")
        self.sock.close()
        if self.writer:
            self.writer.close()
        _LOGGER.debug("Connection closed")
        self.writer = None
        self.reader = None
        self.connected = False

    def start_listener(self):
        """Start the listener."""
        _LOGGER.debug("Starting listener")
        self.listener = asyncio.create_task(self.listen())
        _LOGGER.debug("Listener started")

    def stop_listener(self):
        """Stop the listener."""
        _LOGGER.debug("Stopping listener")
        self.listener.cancel()
        _LOGGER.debug("Listener stopped")

    async def send(self, data: bytes, wait=False) -> bytes | None:
        """Send a command."""
        if not self.writer:
            _LOGGER.error("Not connected. Call connect() first")

        self.writer.write(data)
        await self.writer.drain()
        if wait:
            data = await self.reader.read(1024)
            if not data:
                raise ConnectionResetError("No response received.")
            return data

        return None

    async def listen(self):
        """Listen for incoming data from Zone Touch 3 controller."""
        if not self.reader:
            _LOGGER.debug("Not connected. Call connect() first")
            return

        try:
            while True:
                data = await self.reader.read(1024)
                if not data:
                    raise ConnectionResetError("Connection closed by server.")  # noqa: TRY301
                ztm = ZoneTouchMessage(data)
                self.state.updateFromMessage(ztm)
                if self.on_state_update:
                    self.on_state_update(self.state)
        except asyncio.CancelledError:
            _LOGGER.debug("Listener task cancelled")
        except (
            ConnectionAbortedError,
            ConnectionResetError,
            BrokenPipeError,
        ) as ex:
            _LOGGER.debug("Connection lost (%s) - Reconnecting in 5 seconds", ex)
            await asyncio.sleep(5)
            await self.connect()
            self.start_listener()
        except Exception as ex:
            _LOGGER.error(ex, stack_info=True)
            _LOGGER.debug("Connection lost (%s) - Reconnecting in 5 seconds", ex)
            await asyncio.sleep(5)
            await self.connect()
            self.start_listener()

    def getPacketFetchFullState(self):
        packet = DataPacket()
        packet.id = 1
        packet.addr_dest = self.ADDRESS_CONSOLE
        packet.addr_src = self.ADDRESS_REMOTE
        packet.command = self.COMMAND_EXPAND
        return self.__createFullPacket(packet)

    def __createFullPacket(self, packet):
        header = struct.pack(
            ">BBBB",
            self.PROTOCOL_HEAD_S,
            self.PROTOCOL_HEAD_S,
            self.PROTOCOL_HEAD_S,
            self.PROTOCOL_HEAD_E,
        )

        data = struct.pack(">BBB", packet.addr_dest, packet.addr_src, packet.id)
        data += struct.pack(">B", packet.command)
        data += struct.pack(">H", 2)
        data += struct.pack(">H", self.EX_DATA_FULL_STATE)

        crc = modbus_crc.crc16(data)

        return header + data + struct.pack("<BB", crc[1], crc[0])
