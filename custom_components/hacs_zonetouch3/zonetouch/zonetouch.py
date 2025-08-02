"""ZoneTouch class."""

import asyncio
from collections.abc import Callable
import logging
import socket
import struct
from typing import Any

from .message import ZoneTouchMessage
from .messages.fullstate import FullState
from .messages.spill import Spill
from .state import ZoneTouch3State

_LOGGER = logging.getLogger(__name__)


class ZoneTouch3Exception(Exception):
    """Base class for errors throw by ZoneTouch3."""

    def __init__(self, reason: str | None = None) -> None:
        """Init the exception."""
        self.reason = reason


class ZoneTouch3ClientError(ZoneTouch3Exception):
    """Exception to indicate a general API error."""


class ZoneTouch3ConnectionFailedException(ZoneTouch3Exception):
    """Exception to indicate a general API error."""


class ZoneTouch:
    "ZoneTouch class."

    def __init__(
        self,
        host: str,
        port: int,
        on_state_update: Callable,
        on_disconnect: Callable,
    ) -> None:
        """Sample API Client."""
        self._host = host
        self._port = port
        self.sock: socket.socket
        self.reader: asyncio.StreamReader
        self.writer: asyncio.StreamWriter
        self.queue: asyncio.Queue = asyncio.Queue()
        self.pending_commands: dict[int, asyncio.Future[Any]] = {}
        self.connected = False
        self.on_state_update = on_state_update
        self.on_disconnect = on_disconnect
        self.listener: asyncio.Task
        self.state = ZoneTouch3State()

    async def async_get_full_state(self) -> ZoneTouch3State | None:
        """Get data from the API."""
        full_state_command = FullState().build_packet()
        data = await self.send(full_state_command, True)
        if data:
            self.state = ZoneTouch3State.from_bytes(data)

            spill_state_command = Spill().build_packet()
            spill_response = await self.send(spill_state_command, True)
            spill_message = Spill.from_bytes(spill_response)
            if spill_message:
                for group in self.state.groups.values():
                    group.is_spill_set = group.id in spill_message.groups

            return self.state

        return None

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

    async def queue_command(self, data: bytes):
        """Add commands to queue."""
        await self.queue.put(data)

    async def send(self, data: bytes, wait=False) -> bytes | None:
        """Send a command."""
        if not self.writer:
            _LOGGER.error("Not connected. Call connect() first")

        _LOGGER.debug("-> %s", data.hex())
        self.writer.write(data)
        await self.writer.drain()
        if wait:
            data = await self.reader.read(1024)
            if not data:
                raise ConnectionResetError("No response received.")
            return data

        return None

    async def send_queue(self) -> bytes | None:
        """Send queue processor."""
        while True:
            data = await self.queue.get()
            msg_id: int = struct.unpack_from(">B", data, 6)[0]
            future = asyncio.get_event_loop().create_future()
            self.pending_commands[msg_id] = future
            _LOGGER.debug("-> %s", data.hex())
            self.writer.write(data)
            await self.writer.drain()

            try:
                await asyncio.wait_for(future, timeout=10)
                _LOGGER.debug("Received response for msg_id (%d)", msg_id)
            except TimeoutError:
                _LOGGER.debug("Timeout waiting for response to msg_id (%d)", msg_id)
            finally:
                self.pending_commands.pop(msg_id, None)

            self.queue.task_done()

    def start_send_queue(self):
        """Start processing the send queue."""
        _LOGGER.debug("Starting send queue")
        self.listener = asyncio.create_task(self.send_queue())
        _LOGGER.debug("Send queue started")

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
                future = self.pending_commands.get(ztm.message_id)
                if future and not future.done():
                    future.set_result(True)
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
            self.start_send_queue()
        except Exception as ex:
            _LOGGER.error(ex, stack_info=True, exc_info=True)
            _LOGGER.debug("Connection lost (%s) - Reconnecting in 5 seconds", ex)
            await asyncio.sleep(5)
            await self.connect()
            self.start_listener()
            self.start_send_queue()
