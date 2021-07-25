import asyncio
import functools
import json
import logging
import signal
import platform
import uuid
from multiprocessing.pool import ThreadPool

import websockets
from websockets.exceptions import WebSocketException


logging.basicConfig(level=logging.DEBUG)


class WSServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
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
        self.clients[id] = {'socket': websocket}
        self.on_connect(id, websocket)
        return id

    def on_connect(self, id: str, websocket):
        self.logger.info(f'Client \'{id}\' connected.')

    def _on_disconnect(self, id: str, websocket):
        del self.clients[id]
        self.on_disconnect(id, websocket)
        return id

    def on_disconnect(self, id: str, websocket):
        self.logger.info(f'Client \'{id}\' disconnected.')

    async def handler(self, websocket, path):
        id = self._on_connect(websocket)
        try:
            async for message in websocket:
                message = json.loads(message)
                path = message['path']
                data = message['data'] if 'data' in message else None
                self.logger.debug(f'[{id}] Message received on {path}: {data}')
                if path in self.consumers:
                    consumer = self.consumers[path]
                    response = self.thread_pool.apply(consumer, args=[data, path, id])
                    if response is not None:
                        await websocket.send(json.dumps(response))
                else:
                    await websocket.send(self.on_not_found(data, path, id))
        except WebSocketException:
            pass
        finally:
            self._on_disconnect(id, websocket)

    async def run(self, stop):
        self.server = websockets.serve(self.handler, self.host, self.port)
        await self.server
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


server = WSServer()


@server.on('/')
def echo(payload, path, id):
    return payload


@server.on('/id')
def id(payload, path, id):
    return id


server.start()
