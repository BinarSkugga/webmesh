import asyncio
import threading
import time
from abc import ABC, abstractmethod
from asyncio import Event
from logging import Logger
from threading import Thread
from typing import Optional

from webmesh.message_protocols import AbstractMessageProtocol, SimpleDictProtocol
from webmesh.message_serializers import AbstractMessageSerializer, MessagePackSerializer


class WebMeshComponent(ABC):
    def __init__(self, host: str = '127.0.0.1', port: int = 4269,
                 message_serializer: AbstractMessageSerializer = MessagePackSerializer(),
                 message_protocol: AbstractMessageProtocol = SimpleDictProtocol()):
        self.host = host
        self.port = port
        self.message_serializer = message_serializer
        self.message_protocol = message_protocol

        self.stop = None
        self.started = None
        self.logger: Optional[Logger] = None

    @abstractmethod
    async def run(self):
        self.stop = Event()

    def _start(self):
        while self.stop is None or not self.stop.is_set():
            min_backoff = 1
            max_backoff = 16
            current_backoff = min_backoff
            self.started = threading.Event()

            while not self.started.is_set():
                try:
                    asyncio.run(self.run())
                except RuntimeError:
                    loop = asyncio.get_running_loop()
                    loop.run_until_complete(self.run())
                except OSError:
                    self.logger.warning(f'Failed to sustain connection, reattempting connection in {current_backoff}s...')

                time.sleep(current_backoff)
                current_backoff = min(current_backoff*2, max_backoff)

    def start(self, threaded: bool = False):
        if threaded:
            Thread(target=self._start, daemon=True).start()
        else:
            self._start()

    def close(self):
        self.stop.set()

    def await_started(self, timeout: int = None):
        self.started.wait(timeout)
