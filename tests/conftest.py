import logging
from time import sleep

import pytest

from webmesh.webmesh_client import WebMeshClient
from webmesh.webmesh_server import WebMeshServer, WebMeshConnection

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s, %(name)s, %(asctime)s]'
                                                '[%(threadName)s]'
                                                '[%(filename)s:%(funcName)s:%(lineno)d]:'
                                                ' %(message)s')


@pytest.fixture
def server():
    server = WebMeshServer()

    @server.on('/echo')
    def echo(payload, path, client: WebMeshConnection):
        return payload

    @server.on('/id')
    def id(payload, path, client: WebMeshConnection):
        return client.id

    @server.on('/5sec')
    def sec5(payload, path, client: WebMeshConnection):
        sleep(5)
        return client.id

    try:
        server.start(threaded=True)
        server.await_started()
        yield server
    finally:
        server.close()


@pytest.fixture
def client(server):
    client = WebMeshClient()
    try:
        client.start(threaded=True)
        client.await_started()
        yield client
    finally:
        client.close()
