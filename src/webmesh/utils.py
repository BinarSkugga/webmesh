import asyncio
from functools import partial
from threading import Event
from typing import Any

from websockets import WebSocketServerProtocol


def blocking_send(socket: WebSocketServerProtocol, message: Any):
    if message is not None:
        loop = socket.loop
        asyncio.run_coroutine_threadsafe(socket.send(message), loop)
    return None


def _callback_wrapper(callback, future):
    callback(future.result())


def async_recv(socket: WebSocketServerProtocol, callback):
    loop = socket.loop
    callback = partial(_callback_wrapper, callback)

    future = asyncio.run_coroutine_threadsafe(socket.recv(), loop)
    future.add_done_callback(callback)
    return future


def _sync_callback(event, _):
    event.set()


def blocking_recv(socket: WebSocketServerProtocol):
    done_event = Event()
    callback = partial(_sync_callback, done_event)
    future = async_recv(socket, callback)

    done_event.wait()
    return future.result()
