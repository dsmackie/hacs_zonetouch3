import asyncio
from collections.abc import Callable
from dataclasses import dataclass
import logging
import struct

import modbus_crc

from .message import ZoneTouchMessage
from .state import ZoneTouch3State

_LOGGER = logging.getLogger(__name__)

PROTOCOL_HEAD_S = 0x55
PROTOCOL_HEAD_E = 0xAA


class ZoneTouch3ClientError(Exception):
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
        self, host: str, port: int, on_state_update: Callable | None = None
    ) -> None:
        """Sample API Client."""
        self._host = host
        self._port = port
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.connected = False
        self.on_state_update = on_state_update
        self.listener: asyncio.Task
        self.state = ZoneTouch3State()

    async def async_get_full_state(self) -> ZoneTouch3State:
        """Get data from the API."""
        p = self.getPacketFetchFullState()
        data = await self.send(p, True)
        self.state = ZoneTouch3State.from_bytes(data)
        return self.state

    async def connect(self):
        try:
            conn = asyncio.open_connection(self._host, self._port)
            self.reader, self.writer = await asyncio.wait_for(conn, timeout=5)
            self.connected = True
            _LOGGER.debug("Connected to %s:%s", self._host, self._port)
        except Exception as exception:
            msg = f"Failed to connect: {exception}"
            raise ZoneTouch3ClientError(
                msg,
            ) from exception

    async def close(self) -> None:
        """Close the connection."""
        _LOGGER.debug("Connection closing")
        if self.writer:
            self.writer.close()
            asyncio.create_task(self.writer.wait_closed())  # noqa: RUF006
        _LOGGER.debug("Connection closed")

    def start_listener(self):
        """Start the listener."""
        self.listener = asyncio.create_task(self.listen())

    async def stop_listener(self):
        """Stop the listener."""
        self.listener.cancel()

    async def send(self, data: bytes, wait=False):
        """Send a command."""
        if not self.writer:
            _LOGGER.debug("Not connected. Call connect() first")

        try:
            self.writer.write(data)
            await self.writer.drain()
            if wait:
                return await self.reader.read(1024)
        except Exception as e:
            _LOGGER.error("Error while sending: %s", e)

    async def listen(self):
        if not self.reader:
            _LOGGER.debug("Not connected. Call connect() first")
            return

        try:
            _LOGGER.debug("Listening")
            while self.connected:
                data = await self.reader.read(1024)
                if not data:
                    _LOGGER.debug("Connection closed by server")
                    break
                ztm = ZoneTouchMessage(data)
                self.state.updateFromMessage(ztm)
                self.on_state_update(self.state)
        except asyncio.CancelledError:
            _LOGGER.debug("Listener task cancelled")
        except Exception as ex:
            _LOGGER.debug(ex)
        finally:
            self.connected = False
            await self.close()

    def getPacketFetchFullState(self):
        packet = DataPacket()
        packet.id = 1
        packet.addr_dest = self.ADDRESS_CONSOLE
        packet.addr_src = self.ADDRESS_REMOTE
        packet.command = self.COMMAND_EXPAND
        p = self.__createFullPacket(packet)
        return p

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

        p = header + data + struct.pack("<BB", crc[1], crc[0])

        return p


async def on_state_update_handler(state):
    _LOGGER.debug(state)
