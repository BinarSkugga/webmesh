import socket
from queue import Queue
from typing import Tuple, Type

from webmesh.websocket.abstract_websocket_server import AbstractWebSocketServer
from webmesh.websocket.queued_websocket_connection import QueuedWebSocketConnection


class QueuedWebSocketServer(AbstractWebSocketServer):
    connection_class: Type[QueuedWebSocketConnection]

    def __init__(self, connection_class: Type[QueuedWebSocketConnection] = QueuedWebSocketConnection,
                 socket_timeout: float = 1):
        super().__init__(connection_class, socket_timeout)
        self.queue = Queue()

    def on_new_connection(self, new_client: Tuple[socket.socket, tuple]):
        return self.connection_class(new_client, self.queue)

    def process_messages(self):
        while not self.queue.empty():
            target, message = self.queue.get()
            if target == '__disconnected__':
                self.connections.pop(message)
            else:
                # Handler here
                pass
