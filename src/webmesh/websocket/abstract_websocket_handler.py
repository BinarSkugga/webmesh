from abc import ABC, abstractmethod
from typing import Any, Optional

from webmesh.websocket.abstract_websocket_connection import AbstractWebSocketConnection


class AbstractWebSocketHandler(ABC):
    @abstractmethod
    def on_connect(self, connection: AbstractWebSocketConnection):
        pass

    @abstractmethod
    def on_message(self, connection: AbstractWebSocketConnection, path: str, data: Any):
        pass

    @abstractmethod
    def on_disconnect(self, connection: AbstractWebSocketConnection):
        pass
