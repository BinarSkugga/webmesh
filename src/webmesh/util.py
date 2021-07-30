import socket
import time
from io import StringIO, BytesIO
from typing import Union

from wsproto.events import Ping, Request, AcceptConnection, CloseConnection, TextMessage, BytesMessage, RejectData, \
    Event, RejectConnection


def exponential_backoff(min_backoff: float = 1, max_backoff: float = 16, exceptions: tuple = (Exception,)):
    def wrapper(func):
        def run(*args, **kwargs):
            current_backoff = min_backoff
            while True:
                try:
                    yield func(*args, **kwargs), current_backoff
                    current_backoff = min_backoff
                except exceptions as e:
                    yield e, current_backoff
                    time.sleep(current_backoff)
                    current_backoff = min(current_backoff*2, max_backoff)
        return run
    return wrapper


def _handle_proto(ws, read_buffer_size: int, text_buffer: StringIO = None, bytes_buffer: BytesIO = None) \
        -> Union[bool, str, Event]:
    try:
        ws.recv(read_buffer_size)
        for event in ws.events():
            if isinstance(event, Ping):
                ws.send(event.response())
                return event
            elif isinstance(event, CloseConnection):
                ws.send(event.response())
                return event
            elif isinstance(event, TextMessage):
                if text_buffer is not None:
                    text_buffer.write(event.data)
                    if event.message_finished:
                        return text_buffer.getvalue()
            elif isinstance(event, BytesMessage):
                if bytes_buffer is not None:
                    bytes_buffer.write(event.data)
                    if event.message_finished:
                        ws.send(RejectData(bytes_buffer.getvalue()))
            else:
                if ws.connection.client:
                    if isinstance(event, AcceptConnection):
                        return event
                    elif isinstance(event, RejectConnection):
                        return event
                else:
                    if isinstance(event, Request):
                        ws.send(AcceptConnection())
                        return event
    except socket.timeout:
        return True
