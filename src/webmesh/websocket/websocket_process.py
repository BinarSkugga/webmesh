import logging
import threading
import typing
from io import StringIO

from wsproto import ConnectionType, WSConnection
from wsproto.events import TextMessage

from webmesh.message_protocols import AbstractMessageProtocol
from webmesh.message_serializers import AbstractMessageSerializer
from webmesh.util import _handle_proto
from webmesh.websocket.websocket_connection import WebSocketConnection


if typing.TYPE_CHECKING:
    from webmesh.websocket.websocket_server import AbstractWebSocketHandler


class WebSocketClientProcess:
    def __init__(self, handler: 'AbstractWebSocketHandler', connection: WebSocketConnection,
                 read_buffer_size: int,
                 serializer: AbstractMessageSerializer,
                 protocol: AbstractMessageProtocol):
        self.connection: WebSocketConnection = connection
        self.read_buffer_size = read_buffer_size
        self.logger = None
        self.stop_event = None

        self.handler = handler
        self.serializer = serializer
        self.protocol = protocol

    def close(self, sig=None, term=None):
        self.stop_event.set()

    def listen(self):
        self.logger = logging.getLogger(f'websocket.client')
        self.stop_event = threading.Event()

        with self.connection.context() as ws:
            ws.connection = WSConnection(ConnectionType.SERVER)
            ws.logger = self.logger
            txt_buffer = StringIO()

            self.on_connect(ws)
            data = True
            while data and not self.stop_event.is_set():
                data = _handle_proto(ws, self.read_buffer_size, txt_buffer)
                if isinstance(data, str):
                    self.on_text_message(ws, data)
            self.on_disconnect(ws)
            ws.close()
        return ws.id

    def on_connect(self, connection: WebSocketConnection):
        self.logger.info(f'Client {self.connection.id} connected')
        self.handler.on_connect(connection)

    def on_text_message(self, connection: WebSocketConnection, data: str):
        deserialized = self.serializer.deserialize(data)
        unpacked = self.protocol.unpack(deserialized)

        self.logger.debug(f'Received data on connection {self.connection.id} and path {unpacked[0]}: {unpacked[1]}')
        response = self.handler.on_message(connection, *unpacked)
        if response is not None:
            packed = self.protocol.pack(unpacked[0], response)
            serialized = self.serializer.serialize(packed)
            connection.send(TextMessage(data=serialized))

    def on_disconnect(self, connection: WebSocketConnection):
        self.handler.on_disconnect(connection)
        self.logger.info(f'Client {self.connection.id} disconnected')
