import functools
import logging
from typing import Any, Optional, Type

from webmesh.message_protocols import AbstractMessageProtocol, SimpleDictProtocol
from webmesh.message_serializers import MessagePackSerializer, AbstractMessageSerializer
from webmesh.websocket.websocket_connection import WebSocketConnection
from webmesh.websocket.websocket_server import WebSocketServer, AbstractWebSocketHandler


class WebMeshHandler(AbstractWebSocketHandler):
    def __init__(self):
        self.consumers = {}

    def on_message(self, connection: WebSocketConnection, path: str, data: Any) -> Optional[Any]:
        if path in self.consumers:
            consumer = self.consumers[path]
            return consumer(data, path, connection)
        else:
            # Not found stuff
            pass

    def on(self, path):
        def wrapper(func):
            @functools.wraps(func)
            def run(message, path, connection):
                connection.logger.debug(f'Message received on {path}: {message}')
                return func(message, path, connection)

            self.consumers[path] = run
            return run
        return wrapper


class WebMeshServer(WebSocketServer):
    def __init__(self,
                 host: str = '0.0.0.0', port: int = 4269,
                 debug: bool = False, max_parallelism: int = 5,
                 serializer: AbstractMessageSerializer = MessagePackSerializer(),
                 protocol: AbstractMessageProtocol = SimpleDictProtocol()
                 ):
        handler = WebMeshHandler()
        super().__init__(handler, serializer, protocol, max_parallelism=max_parallelism)

        self.host = host
        self.port = port

        self.debug = debug
        self.logger = logging.getLogger('webmesh.server')

        self.consumers = {}
        self.on = handler.on

    def listen(self, host: str = '0.0.0.0', port: int = 4269, blocking: bool = False):
        super().listen(host, port, blocking)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s, %(name)s, %(asctime)s]'
                                                    '[%(threadName)s]'
                                                    '[%(filename)s:%(funcName)s:%(lineno)d]:'
                                                    ' %(message)s')
    server = WebMeshServer()

    @server.on('/test')
    def _test(payload, path, connection: WebSocketConnection):
        print(path, payload, connection.id)

    server.listen()
    server.close_event.wait()
