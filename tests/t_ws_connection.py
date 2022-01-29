from typing import Any

from webmesh.websocket.abstract_websocket_connection import AbstractWebSocketConnection


class TestWebSocketConnection(AbstractWebSocketConnection):
    def on_connect(self):
        self.logger.info('Connected')

    def on_disconnect(self):
        self.logger.info('Disconnected')

    def on_message(self, target: str, message: Any):
        self.logger.info(target, message)
