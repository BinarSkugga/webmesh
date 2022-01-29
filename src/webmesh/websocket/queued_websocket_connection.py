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
        self.logger.info('Connected')

    def on_disconnect(self):
        self.queue.put(('__disconnected__', self.id))
        self.logger.info('Disconnected')

    def on_message(self, target: str, message: Any):
        self.logger.info(f'Received message at {target} !')
        self.logger.debug(f'Message content at {target}: {message}')
        self.queue.put((target, message))
