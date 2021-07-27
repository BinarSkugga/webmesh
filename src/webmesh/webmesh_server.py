import dataclasses
import functools
import logging
import uuid
from multiprocessing.pool import ThreadPool

import websockets
from websockets import WebSocketServerProtocol, WebSocketException

from webmesh.message_protocols import AbstractMessageProtocol, SimpleDictProtocol
from webmesh.message_serializers import AbstractMessageSerializer, MessagePackSerializer
from webmesh.utils import blocking_send
from webmesh.webmesh_component import WebMeshComponent


@dataclasses.dataclass
class WebMeshConnection:
    id: str
    socket: WebSocketServerProtocol
    logger: logging.Logger


class WebMeshServer(WebMeshComponent):
    def __init__(self,
                 host: str = '0.0.0.0', port: int = 4269,
                 debug: bool = False, thread_count: int = 5,
                 message_serializer: AbstractMessageSerializer = MessagePackSerializer(),
                 message_protocol: AbstractMessageProtocol = SimpleDictProtocol()
                 ):
        super().__init__(host, port, message_serializer, message_protocol)

        self.debug = debug
        self.server = None
        self.consumers = {}
        self.clients = {}
        self.logger = logging.getLogger('webmesh.server')
        self.thread_pool = ThreadPool(processes=thread_count)

        if not self.debug:
            logging.getLogger('websockets.server').disabled = True
            logging.getLogger('websockets.protocol').disabled = True
            logging.getLogger('asyncio').disabled = True

    # CORE METHODS ======================================================================

    def on(self, path):
        def wrapper(func):
            @functools.wraps(func)
            def run(message, path, client):
                client.logger.debug(f'Message received on {path}: {message}')
                return func(message, path, client)

            self.consumers[path] = run
            return run
        return wrapper

    def find_and_run(self, message, client):
        deserialized_message = self.message_serializer.deserialize(message)
        m_path, data = self.message_protocol.unpack(deserialized_message)

        if m_path in self.consumers:
            consumer = self.consumers[m_path]
            response = consumer(data, m_path, client)
        else:
            response = self.on_not_found(data, m_path, client)

        if response is not None:
            packed_response = self.message_protocol.pack(m_path, response)
            client.logger.debug(f'Answered request to {m_path}: {packed_response}')

            serialized_response = self.message_serializer.serialize(packed_response)
            return serialized_response

    async def handler(self, websocket: WebSocketServerProtocol, path):
        client = self._on_connect(websocket)
        try:
            response_func = functools.partial(blocking_send, websocket)
            async for message in websocket:
                self.thread_pool.apply_async(self.find_and_run, args=[message, client],
                                             callback=response_func, error_callback=self.logger.error)
        except WebSocketException as e:
            if self.debug:
                self.logger.error(e)
        finally:
            self._on_disconnect(client)

    async def run(self):
        async with websockets.serve(self.handler, self.host, self.port) as ws_server:
            self.server = ws_server
            self.started.set()
            self.logger.info('WebMesh server started.')

            await self.stop.wait()
            self.logger.info('WebMesh server stopped.')

    # CALLBACKS ======================================================================

    def _on_connect(self, websocket):
        id = uuid.uuid4().hex
        self.clients[id] = WebMeshConnection(id, websocket, logging.getLogger(f'webmesh.{id}'))
        self.on_connect(self.clients[id])
        return self.clients[id]

    def _on_disconnect(self, client: WebMeshConnection):
        self.on_disconnect(client)
        del self.clients[client.id]
        return id

    # OVERRIDES ======================================================================

    def on_connect(self, client: WebMeshConnection):
        client.logger.info('Connected.')

    def on_disconnect(self, client: WebMeshConnection):
        client.logger.info('Disconnected.')

    def on_not_found(self, payload, path, client):
        return 'Path not found'
