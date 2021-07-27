import logging
import signal
import socket
import threading
import uuid
from abc import ABC
from functools import partial
from multiprocessing import Pool
from typing import Dict, Type, Any, Optional

from webmesh.message_protocols import AbstractMessageProtocol
from webmesh.message_serializers import AbstractMessageSerializer
from webmesh.websocket.websocket_connection import WebSocketConnection
from webmesh.websocket.websocket_process import WebSocketClientProcess


class AbstractWebSocketHandler(ABC):
    def on_connect(self, connection: WebSocketConnection):
        pass

    def on_message(self, connection: WebSocketConnection, path: str, data: Any) -> Optional[Any]:
        pass

    def on_disconnect(self, connection: WebSocketConnection):
        pass


class WebSocketServer(ABC):
    def __init__(self,
                 handler: AbstractWebSocketHandler,
                 serializer_type: Type[AbstractMessageSerializer],
                 protocol_type: Type[AbstractMessageProtocol],
                 max_parallelism: int = 5,
                 max_conn_backlog: int = 5,
                 read_buffer_size: int = 1024,
                 socket_timeout: float = 1
                 ):
        self.logger = logging.getLogger('websocket.server')
        self.close_event = threading.Event()
        self.handler = handler
        self.serializer_type = serializer_type
        self.protocol_type = protocol_type

        self.max_parallelism = max_parallelism
        self.max_conn_backlog = max_conn_backlog
        self.connections: Dict[str, WebSocketConnection] = {}

        self.socket = None
        self.read_buffer_size = read_buffer_size
        self.socket_timeout = socket_timeout

    def close(self, sig=None, frame=None):
        self.close_event.set()

    def _listen(self, host: str, port: int):
        with Pool(processes=self.max_parallelism) as pool:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            try:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.settimeout(self.socket_timeout)

                self.socket.bind((host, port))
                self.socket.listen(self.max_conn_backlog)

                def _connection_closed(self, id: str):
                    del self.connections[id]
                    self.logger.debug(f'Unregistered client {id}')
                _connection_closed = partial(_connection_closed, self)

                self.logger.info(f'Listening on ws://{host}:{port}...')
                while not self.close_event.is_set():
                    try:
                        conn, addr = self.socket.accept()
                        conn.settimeout(self.socket_timeout)
                        conn.setblocking(True)

                        id = uuid.uuid4().hex
                        peer = WebSocketConnection(id, conn, addr)
                        self.connections[id] = peer

                        process = WebSocketClientProcess(
                            self.handler, peer, self.read_buffer_size,
                            self.serializer_type, self.protocol_type
                        )
                        pool.apply_async(process.listen, callback=_connection_closed)
                    except socket.timeout:
                        pass  # We expect timeouts when there is nothing going on
                    except socket.error:
                        raise
            finally:
                for peer in self.connections.values():
                    peer.close()
                    self.logger.debug(f'Closed peer connection {peer.id}')

                self.socket.close()
                self.logger.info('Server stopped')

    def listen(self, host: str, port: int, blocking: bool = False):
        signal.signal(signal.SIGINT, self.close)
        if blocking:
            self._listen(host, port)
        else:
            threading.Thread(target=self._listen, daemon=True, args=[host, port]).start()
