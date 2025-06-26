import asyncio
from collections.abc import Awaitable
import logging
import math
from typing import TypeVar

_LOGGER = logging.getLogger(__name__)

# Server configuration
HOST = "192.168.1.202"  # Replace with server IP if needed
PORT = 7030  # Replace with the actual server port

T = TypeVar("T")


class Clienta:
    def __init__(
        self, hostname: str, port: int = 7030, timeout: float | None = None
    ) -> None:
        self.hostname = hostname
        self.port = port

        # Connection state
        self._connected: asyncio.Future[None] = asyncio.Future()
        self._lock: asyncio.Lock = asyncio.Lock()
        self.connected = False
        self.listener: asyncio.Task

        if timeout is None:
            timeout = 10
        self.timeout = timeout

    async def connect(self) -> bool:
        """Opens connection to the server, returns True/False if successful/unsuccessful"""
        _LOGGER.debug(f"Connecting to {self.hostname} on port {self.port}")
        try:
            self._reader, self._writer = await asyncio.open_connection(
                self.hostname, self.port
            )
            self._connected.set_result(None)
            if self._connected.done():
                self.connected = True
                self.listener = asyncio.create_task(self.listen_for_data())
                return True
        except OSError as e:
            _LOGGER.warning(f"Could not connect to host {self.hostname}")
            return False

        return False

    async def listen_for_data(self):
        try:
            while True:
                data = await self._reader.read(1024)
                if not data:
                    break  # Connection closed
                _LOGGER.debug(f"Received: {data.hex()}")
        except Exception as ex:
            print("Client disconnected")
        finally:
            self._writer.close()
            await self._writer.wait_closed()

    async def __aenter__(self):
        if self._lock.locked():
            raise Exception("Error message 1")
        await self._lock.acquire()
        try:
            await self.connect(self.hostname, self.port)
        except Exception as ex:
            self._lock.release()
            raise Exception("Error message 2")
        try:
            await self._wait_for(self._connected, timeout=None)
        except Exception as ex:
            raise Exception("Error message 4")

        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        pass

    async def _wait_for(self, fut: Awaitable[T], timeout: float | None) -> T:
        if timeout is None:
            timeout = self.timeout
        # Note that asyncio uses `None` to mean "No timeout". We use `math.inf`.
        timeout_for_asyncio = None if timeout == math.inf else timeout
        try:
            return await asyncio.wait_for(fut, timeout=timeout_for_asyncio)
        except asyncio.TimeoutError:
            msg = "Operation timed out"
            raise Exception("Error message 3") from None
