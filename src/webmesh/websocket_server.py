import asyncio
import functools
import json
import signal
from multiprocessing.pool import ThreadPool

import websockets


class WSServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        self.consumers = {}
        self.thread_pool = ThreadPool()

    def on(self, path):
        def wrapper(func):
            @functools.wraps(func)
            def run(message, path):
                return func(message, path)

            self.consumers[path] = run
            return run
        return wrapper

    def on_not_found(self, payload, path):
        return json.dumps('Path not found')

    async def handler(self, websocket, path):
        with self.thread_pool as pool:
            async for message in websocket:
                message = json.loads(message)
                path = message['path']
                data = message['data'] if 'data' in message else None
                print(f'Message received on {path}: {data}')

                if path in self.consumers:
                    consumer = self.consumers[path]
                    response = pool.apply(consumer, args=[data, path])
                    if response is not None:
                        await websocket.send(json.dumps(response))
                else:
                    await websocket.send(self.on_not_found(data, path))

    async def run(self, stop):
        async with websockets.serve(self.handler, self.host, self.port):
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
def echo(payload, path):
    return payload


@server.on('/add')
def echo(payload, path):
    return str(1+1)


server.start()
