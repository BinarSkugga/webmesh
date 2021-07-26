import asyncio
import threading
from abc import ABC, abstractmethod
from asyncio import Event
from threading import Thread

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
        self.started = threading.Event()

    @abstractmethod
    async def run(self):
        self.stop = Event()

    def _start(self):
        try:
            asyncio.run(self.run())
        except RuntimeError:
            loop = asyncio.get_running_loop()
            loop.run_until_complete(self.run())

    def start(self, threaded: bool = False):
        if threaded:
            Thread(target=self._start, daemon=True).start()
        else:
            self._start()

    def close(self):
        self.stop.set()

    def await_started(self, timeout: int = 5):
        self.started.wait(timeout)
