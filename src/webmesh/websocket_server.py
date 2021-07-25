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
from websockets import WebSocketServerProtocol
from websockets.exceptions import WebSocketException


logging.basicConfig(level=logging.DEBUG)


@dataclasses.dataclass
class WebMeshClient:
    id: str
    socket: WebSocketServerProtocol
    logger: logging.Logger


class WebMeshServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 4269, debug: bool = False):
        self.host = host
        self.port = port
        self.server = None
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
            def run(message, path, id):
                return func(message, path, id)

            self.consumers[path] = run
            return run
        return wrapper

    def on_not_found(self, payload, path, id):
        return json.dumps('Path not found')

    def _on_connect(self, websocket):
        id = uuid.uuid4().hex
        self.clients[id] = WebMeshClient(id, websocket, logging.getLogger(f'webmesh.client.{id}'))
        self.on_connect(self.clients[id])
        return self.clients[id]

    def on_connect(self, client: WebMeshClient):
        client.logger.info(f'Connected.')

    def _on_disconnect(self, client: WebMeshClient):
        self.on_disconnect(client)
        del self.clients[client.id]
        return id

    def on_disconnect(self, client: WebMeshClient):
        client.logger.info(f'Disconnected.')

    async def handler(self, websocket, path):
        client = self._on_connect(websocket)
        try:
            async for message in websocket:
                message = json.loads(message)
                path = message['path']
                data = message['data'] if 'data' in message else None
                client.logger.debug(f'Message received on {path}: {data}')
                if path in self.consumers:
                    consumer = self.consumers[path]
                    response = self.thread_pool.apply(consumer, args=[data, path, client.id])
                    if response is not None:
                        await websocket.send(json.dumps(response))
                else:
                    await websocket.send(self.on_not_found(data, path, client.id))
        except WebSocketException:
            pass
        finally:
            self._on_disconnect(client)

    async def run(self, stop):
        async with websockets.serve(self.handler, self.host, self.port) as ws_server:
            self.server = ws_server
            await stop

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


server = WebMeshServer()


@server.on('/')
def echo(payload, path, id):
    return payload


@server.on('/id')
def id(payload, path, id):
    return id


server.start()
