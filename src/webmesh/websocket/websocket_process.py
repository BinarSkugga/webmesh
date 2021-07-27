import logging
import signal
import socket
import threading
import traceback
import typing
from io import StringIO, BytesIO
from typing import Type, Optional, Union

from wsproto import ConnectionType, WSConnection
from wsproto.events import Ping, Request, AcceptConnection, CloseConnection, TextMessage, \
    BytesMessage, RejectData

from webmesh.message_protocols import AbstractMessageProtocol
from webmesh.message_serializers import AbstractMessageSerializer
from webmesh.websocket.websocket_connection import WebSocketConnection


if typing.TYPE_CHECKING:
    from webmesh.websocket.websocket_server import AbstractWebSocketHandler


class WebSocketClientProcess:
    def __init__(self, handler: 'AbstractWebSocketHandler', connection: WebSocketConnection,
                 read_buffer_size: int,
                 serializer_type: Type[AbstractMessageSerializer],
                 protocol_type: Type[AbstractMessageProtocol]):
        self.connection: WebSocketConnection = connection
        self.read_buffer_size = read_buffer_size
        self.logger = None
        self.stop_event = None

        self.serializer_type = serializer_type
        self.protocol_type = protocol_type

        self.handler = handler
        self.serializer: Optional[AbstractMessageSerializer] = None
        self.protocol: Optional[AbstractMessageProtocol] = None

    def close(self, sig=None, term=None):
        self.stop_event.set()

    def listen(self):
        signal.signal(signal.SIGINT, self.close)

        self.logger = logging.getLogger(f'websocket.{self.connection.id}')
        self.stop_event = threading.Event()
        self.serializer = self.serializer_type()
        self.protocol = self.protocol_type()

        with self.connection.context() as ws:
            ws.connection = WSConnection(ConnectionType.SERVER)
            ws.logger = self.logger

            txt_buffer = StringIO()
            byt_buffer = BytesIO()

            self.on_connect(ws)
            data = True
            while data and not self.stop_event.is_set():
                data = _handle_proto(ws, self.read_buffer_size, txt_buffer, byt_buffer)
                if isinstance(data, str):
                    self.on_text_message(ws, data)
            self.on_disconnect(ws)

            return ws.id

    def on_connect(self, connection: WebSocketConnection):
        self.logger.info('Client connected')
        self.handler.on_connect(connection)

    def on_text_message(self, connection: WebSocketConnection, data: str):
        deserialized = self.serializer.deserialize(data)
        unpacked = self.protocol.unpack(deserialized)

        self.logger.debug(f'Received data on path {unpacked[0]}: {unpacked[1]}')
        response = self.handler.on_message(connection, *unpacked)
        if response is not None:
            packed = self.protocol.pack(unpacked[0], response)
            serialized = self.serializer.serialize(packed)
            connection.send(TextMessage(data=serialized))

    def on_disconnect(self, connection: WebSocketConnection):
        self.handler.on_disconnect(connection)
        self.logger.info('Client disconnected')


def _handle_proto(ws,
                  read_buffer_size: int,
                  text_buffer: StringIO,
                  bytes_buffer: BytesIO) -> Union[bool, str]:
    try:
        ws.recv(read_buffer_size)
        for event in ws.events():
            if isinstance(event, Ping):
                ws.send(event.response())
            elif isinstance(event, Request):
                ws.send(AcceptConnection())
            elif isinstance(event, CloseConnection):
                ws.send(event.response())
                return False
            elif isinstance(event, TextMessage):
                text_buffer.write(event.data)
                if event.message_finished:
                    return text_buffer.getvalue()
            elif isinstance(event, BytesMessage):
                bytes_buffer.write(event.data)
                if event.message_finished:
                    ws.send(RejectData(bytes_buffer.getvalue()))
    except socket.timeout:
        pass
    except Exception:
        traceback.print_exc()
        return False

    return True
