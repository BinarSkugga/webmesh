import dataclasses
import logging
import socket
from contextlib import contextmanager
from typing import Tuple

from wsproto import WSConnection, ConnectionState
from wsproto.events import CloseConnection


@dataclasses.dataclass
class WebSocketConnection:
    id: str
    sock: socket.socket
    addr: Tuple[str, int]
    connection: WSConnection = None
    logger: logging.Logger = None

    @contextmanager
    def context(self) -> 'WebSocketConnection':
        try:
            yield self
        finally:
            self.connection.receive_data(None)
            self.close()

    def events(self):
        return self.connection.events()

    def send(self, data):
        if self.connection.state != ConnectionState.CLOSED:
            encoded = self.connection.send(data)
            self.sock.send(encoded)

    def recv(self, buffer_size: int):
        if self.connection.state != ConnectionState.CLOSED:
            data = self.sock.recv(buffer_size)
            self.connection.receive_data(data)
            return data

    def close(self, code: int = 1000):
        if self.connection.state != ConnectionState.CLOSED:
            self.send(CloseConnection(code))
