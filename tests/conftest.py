import logging
from time import sleep

import pytest

from webmesh.webmesh_server import WebMeshServer
from webmesh.websocket.websocket_connection import WebSocketConnection

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s, %(name)s, %(asctime)s]'
                                                '[%(threadName)s]'
                                                '[%(filename)s:%(funcName)s:%(lineno)d]:'
                                                ' %(message)s')


@pytest.fixture(scope='module')
def server():
    server = WebMeshServer()

    @server.on('/echo')
    def echo(payload, path, connection: WebSocketConnection):
        return payload

    @server.on('/id')
    def id(payload, path, connection: WebSocketConnection):
        return connection.id

    @server.on('/inc')
    def inc(payload, path, connection: WebSocketConnection):
        if not hasattr(connection, 'counter'):
            setattr(connection, 'counter', 0)
        connection.counter += 1

    @server.on('/getinc')
    def getinc(payload, path, connection: WebSocketConnection):
        if hasattr(connection, 'counter'):
            return connection.counter
        else:
            return 0

    @server.on('/3sec')
    def sec3(payload, path, connection: WebSocketConnection):
        sleep(3)
        return connection.id

    try:
        server.listen()
        yield server
    finally:
        server.close()
