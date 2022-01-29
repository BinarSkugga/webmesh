import socket
from queue import Queue
from typing import Any, Tuple

from wsproto import ConnectionType

from webmesh.message_protocols import SimpleDictProtocol
from webmesh.message_serializers import AbstractMessageSerializer, StandardJsonSerializer
from webmesh.websocket.abstract_websocket_connection import AbstractWebSocketConnection


class QueuedWebSocketConnection(AbstractWebSocketConnection):
    def __init__(self, connection: Tuple[socket.socket, tuple], queue: Queue,
                 serializer: AbstractMessageSerializer = StandardJsonSerializer(SimpleDictProtocol()),
                 connection_type: ConnectionType = ConnectionType.SERVER):
        super().__init__(connection, serializer, connection_type)
        self.queue = queue

    def on_connect(self):
        self.queue.put(('__connected__', self, None))

    def on_disconnect(self):
        self.queue.put(('__disconnected__', self, None))

    def on_message(self, target: str, message: Any):
        self.queue.put((target, self, message))
