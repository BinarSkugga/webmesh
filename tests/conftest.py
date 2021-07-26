import logging
from time import sleep

import pytest

from webmesh.webmesh_client import WebMeshClient
from webmesh.webmesh_server import WebMeshServer, WebMeshConnection

logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s, %(name)s, %(asctime)s]'
                                                '[%(threadName)s]'
                                                '[%(filename)s:%(funcName)s:%(lineno)d]:'
                                                ' %(message)s')


@pytest.fixture(scope='module')
def server():
    server = WebMeshServer()

    @server.on('/echo')
    def echo(payload, path, client: WebMeshConnection):
        return payload

    @server.on('/id')
    def id(payload, path, client: WebMeshConnection):
        return client.id

    @server.on('/inc')
    def inc(payload, path, client: WebMeshConnection):
        if not hasattr(client, 'counter'):
            setattr(client, 'counter', 0)
        client.counter += 1

    @server.on('/getinc')
    def getinc(payload, path, client: WebMeshConnection):
        if hasattr(client, 'counter'):
            return client.counter
        else:
            return 0

    @server.on('/3sec')
    def sec3(payload, path, client: WebMeshConnection):
        sleep(3)
        return client.id

    try:
        server.start(threaded=True)
        yield server
    finally:
        server.close()


@pytest.fixture(scope='module')
def client():
    client = WebMeshClient()
    try:
        client.start(threaded=True)
        client.await_started()
        yield client
    finally:
        client.close()


@pytest.fixture
def client1():
    client = WebMeshClient()
    try:
        client.start(threaded=True)
        client.await_started()
        yield client
    finally:
        client.close()


@pytest.fixture
def client2():
    client = WebMeshClient()
    try:
        client.start(threaded=True)
        client.await_started()
        yield client
    finally:
        client.close()
