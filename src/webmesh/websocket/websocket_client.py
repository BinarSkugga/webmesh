import logging
import signal
import socket
import threading
import uuid
from abc import ABC, abstractmethod
from io import StringIO
from typing import Any

from wsproto import WSConnection, ConnectionType
from wsproto.events import Request, AcceptConnection, CloseConnection, RejectConnection, TextMessage

from webmesh.message_protocols import AbstractMessageProtocol
from webmesh.message_serializers import AbstractMessageSerializer
from webmesh.util import _handle_proto, exponential_backoff
from webmesh.websocket.websocket_connection import WebSocketConnection


def _ep_wrapper(host, port, logger, generator):
    for attempt, backoff in generator:
        if isinstance(attempt, Exception):
            logger.error(f'Failed to connect to ws://{host}:{port}, reattempting in {backoff}s...')


class WebSocketClient(ABC):
    def __init__(self, serializer: AbstractMessageSerializer, protocol: AbstractMessageProtocol,
                 read_buffer_size: int = 1024):
        self.logger = logging.getLogger(f'websocket.client')
        self.read_buffer_size = read_buffer_size
        self.disconnect_event = threading.Event()
        self.connect_event = threading.Event()
        self.serializer = serializer
        self.protocol = protocol
        self.connection = None

    def close(self, sig=None, frame=None):
        self.disconnect_event.set()

    def await_connected(self, timeout=None):
        self.connect_event.wait(timeout)

    def emit(self, target: str, data: Any):
        packed_message = self.protocol.pack(target, data)
        serialized_message = self.serializer.serialize(packed_message)
        self.connection.send(TextMessage(serialized_message))

    def _connect(self, host: str, port: int):
        ws = WSConnection(ConnectionType.CLIENT)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        id = uuid.uuid4().hex
        self.connection = WebSocketConnection(id, sock, (host, port))
        self.connection.connection = ws
        self.connection.logger = self.logger

        with self.connection.context() as ws:
            ws.sock.settimeout(1)
            ws.sock.connect((host, port))
            ws.send(Request(host=f'ws://{host}:{port}', target='/'))

            data = True
            txt_buffer = StringIO()

            while data and not self.disconnect_event.is_set():
                data = _handle_proto(ws, self.read_buffer_size, txt_buffer)
                if isinstance(data, AcceptConnection):
                    self.on_connect(ws)
                    self.connect_event.set()
                if isinstance(data, RejectConnection):
                    data = False
                if isinstance(data, CloseConnection):
                    self.on_disconnect(ws)
            ws.close()

    def connect(self, host: str, port: int, blocking: bool = False):
        signal.signal(signal.SIGINT, self.close)

        eb_func = exponential_backoff(predicate=lambda: not self.disconnect_event.is_set())(self._connect)
        if blocking:
            _ep_wrapper(host, port, self.logger, eb_func(host, port))
        else:
            threading.Thread(target=_ep_wrapper, daemon=True,
                             args=[host, port, self.logger, eb_func(host, port)]).start()

    def _on_connect(self, ws: WebSocketConnection):
        self.on_connect(ws)

    @abstractmethod
    def on_connect(self, ws: WebSocketConnection):
        pass

    def _on_disconnect(self, ws: WebSocketConnection):
        self.on_disconnect(ws)

    @abstractmethod
    def on_disconnect(self, ws: WebSocketConnection):
        pass
