import asyncio
import threading
from abc import ABC, abstractmethod
from asyncio import Event
from threading import Thread


class WebMeshComponent(ABC):
    def __init__(self):
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
