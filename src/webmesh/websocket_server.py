import asyncio
import functools
import json
import signal
import uuid
from multiprocessing.pool import ThreadPool

import websockets
from websockets.exceptions import WebSocketException


class WSServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        self.server = None
        self.consumers = {}
        self.clients = {}
        self.thread_pool = ThreadPool()

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

    def on_connect(self, websocket):
        id = uuid.uuid4().hex
        self.clients[id] = websocket
        print(f'[{id}] Client connected !')
        return id

    async def handler(self, websocket, path):
        id = self.on_connect(websocket)
        try:
            async for message in websocket:
                message = json.loads(message)
                path = message['path']
                data = message['data'] if 'data' in message else None
                print(f'[{id}] Message received on {path}: {data}')
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
            del self.clients[id]
            print(f'[{id}] Client disconnected !')

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
