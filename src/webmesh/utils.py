import asyncio
from threading import Event
from typing import Any

from websockets import WebSocketServerProtocol


def sync_send(socket: WebSocketServerProtocol, message: Any):
    if message is not None:
        loop = socket.loop
        asyncio.run_coroutine_threadsafe(socket.send(message), loop)
    return None


def sync_recv(socket: WebSocketServerProtocol):
    loop = socket.loop
    done_event = Event()

    def _set(_):
        done_event.set()

    future = asyncio.run_coroutine_threadsafe(socket.recv(), loop)
    future.add_done_callback(_set)
    done_event.wait()

    return future.result()
