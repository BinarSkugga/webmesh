import logging
import socket
from concurrent.futures import ThreadPoolExecutor

import pytest

from webmesh.websocket.queued_websocket_server import QueuedWebSocketServer

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s, %(name)s, %(asctime)s]'
                                                '[%(threadName)s]'
                                                '[%(filename)s:%(funcName)s:%(lineno)d]:'
                                                ' %(message)s')


@pytest.fixture(scope='module')
def basic_server():
    server = QueuedWebSocketServer()
    try:
        server.start('0.0.0.0', 4269)
        server.await_started()

        yield server
    finally:
        server.close()
