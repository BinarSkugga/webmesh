import asyncio
import dataclasses
import functools
import json
import logging
import signal
import platform
import uuid
from multiprocessing.pool import ThreadPool

import websockets
from websockets import WebSocketServerProtocol, WebSocketException

from webmesh.message_protocols import AbstractMessageProtocol, SimpleDictProtocol
from webmesh.message_serializers import AbstractMessageSerializer, MessagePackSerializer, StandardJsonSerializer


@dataclasses.dataclass
class WebMeshConnection:
    id: str
    socket: WebSocketServerProtocol
    logger: logging.Logger


class WebMeshServer:
    def __init__(self,
                 host: str = '0.0.0.0', port: int = 4269,
                 debug: bool = False,
                 message_serializer: AbstractMessageSerializer = MessagePackSerializer(),
                 message_protocol: AbstractMessageProtocol = SimpleDictProtocol()
                 ):
        self.host = host
        self.port = port
        self.server = None
        self.message_serializer = message_serializer
        self.message_protocol = message_protocol
        self.consumers = {}
        self.clients = {}
        self.thread_pool = ThreadPool()
        self.logger = logging.getLogger('webmesh.server')

        if not debug:
            logging.getLogger('websockets.server').disabled = True
            logging.getLogger('websockets.protocol').disabled = True
            logging.getLogger('asyncio').disabled = True

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
            packed_response = self.message_protocol.pack(response)
            serialized_response = self.message_serializer.serialize(packed_response)
            return serialized_response

    def on_not_found(self, payload, path, client):
        return json.dumps('Path not found')

    def _on_connect(self, websocket):
        id = uuid.uuid4().hex
        self.clients[id] = WebMeshConnection(id, websocket, logging.getLogger(f'webmesh.connection.{id}'))
        self.on_connect(self.clients[id])
        return self.clients[id]

    def on_connect(self, client: WebMeshConnection):
        client.logger.info(f'Connected.')

    def _on_disconnect(self, client: WebMeshConnection):
        self.on_disconnect(client)
        del self.clients[client.id]
        return id

    def on_disconnect(self, client: WebMeshConnection):
        client.logger.info(f'Disconnected.')

    async def handler(self, websocket: WebSocketServerProtocol, path):
        client = self._on_connect(websocket)
        try:
            def _sync_send(message):
                if message is not None:
                    loop = websocket.loop
                    asyncio.run_coroutine_threadsafe(websocket.send(message), loop)

            async for message in websocket:
                self.thread_pool.apply_async(self.find_and_run, args=[message, client], callback=_sync_send)
        except WebSocketException:
            # traceback.print_exc()
            pass
        finally:
            self._on_disconnect(client)

    async def run(self, stop):
        async with websockets.serve(self.handler, self.host, self.port) as ws_server:
            self.server = ws_server
            self.logger.info('WebMesh server started.')
            await stop
            self.logger.info('WebMesh server stopped.')

    def start(self):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        stop = loop.create_future()
        if platform.system == 'Linux':
            loop.add_signal_handler(signal.SIGINT, stop.set_result, None)
            loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

        loop.run_until_complete(self.run(stop))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s, %(name)s, %(asctime)s]'
                                                    '[%(threadName)s]'
                                                    '[%(filename)s:%(funcName)s:%(lineno)d]:'
                                                    ' %(message)s')
    server = WebMeshServer(message_serializer=StandardJsonSerializer())


    @server.on('/')
    def echo(payload, path, client: WebMeshConnection):
        return payload


    @server.on('/id')
    def id(payload, path, client: WebMeshConnection):
        return client.id


    server.start()