from typing import Any

from webmesh.websocket.abstract_websocket_connection import AbstractWebSocketConnection
from webmesh.websocket.abstract_websocket_handler import AbstractWebSocketHandler


class BasicWebSocketHandler(AbstractWebSocketHandler):
    def on_connect(self, connection: AbstractWebSocketConnection):
        print(f'Client {connection.id} connected.')

    def on_message(self, connection: AbstractWebSocketConnection, path: str, data: Any):
        print(f'Received message on {path}: {data}')

    def on_disconnect(self, connection: AbstractWebSocketConnection):
        print(f'Client {connection.id} disconnected.')