import logging
import signal
import socket
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, Type, Tuple

from webmesh.websocket.abstract_websocket_connection import AbstractWebSocketConnection
from webmesh.websocket.abstract_websocket_handler import AbstractWebSocketHandler


class AbstractWebSocketServer(ABC):
    def __init__(self,
                 handler: AbstractWebSocketHandler,
                 connection_class: Type[AbstractWebSocketConnection],
                 socket_timeout: float = 1
                 ):
        self.logger = logging.getLogger('websocket.server')
        self.stop_event = threading.Event()
        self.started_event = threading.Event()
        self.pool = ThreadPoolExecutor(max_workers=5)
        self.handler = handler

        self.connection_class = connection_class
        self.connections: Dict[str, AbstractWebSocketConnection] = {}

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.settimeout(socket_timeout)

    @abstractmethod
    def on_new_connection(self, new_client: Tuple[socket.socket, tuple]):
        pass

    def close(self, sig=None, frame=None):
        self.stop_event.set()

    def await_started(self, timeout=None):
        self.started_event.wait(timeout)

    def process_messages_loop(self):
        while not self.stop_event.is_set():
            self.process_messages()

    @abstractmethod
    def process_messages(self):
        pass

    def listen(self, host: str, port: int):
        try:
            self.socket.bind((host, port))
            self.socket.listen()

            self.logger.info('Listening on ws://127.0.0.1:4269')
            self.started_event.set()

            self.pool.submit(self.process_messages_loop)
            while not self.stop_event.is_set():
                try:
                    new_client = self.socket.accept()
                    connection = self.on_new_connection(new_client)
                    self.connections[connection.id] = connection
                    self.pool.submit(connection.listen)
                except socket.timeout:
                    pass  # We expect timeouts when there is nothing going on
                except socket.error:
                    raise
        finally:
            for c in self.connections.values():
                c.close()
            self.socket.close()

    def start(self, host: str, port: int, blocking: bool = False):
        signal.signal(signal.SIGINT, self.close)
        if blocking:
            self.listen(host, port)
        else:
            threading.Thread(target=self.listen, daemon=True, args=[host, port]).start()
