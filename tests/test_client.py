import asyncio
import time
from threading import Event

from webmesh.webmesh_client import WebMeshClient
from webmesh.webmesh_server import WebMeshServer, WebMeshConnection


def test_reconnect_attemps():
    client = WebMeshClient(port=4270)
    client.start(threaded=True)

    time.sleep(10)

    server = WebMeshServer(port=4270)

    @server.on('/echo')
    def echo(payload, path, client: WebMeshConnection):
        return payload

    server.start(threaded=True)
    server.await_started()
    client.await_started()  # Client should work even if the server was started late

    assert client.call('/echo', 'hello') == 'hello'

    client.close()
    server.close()


def test_connection_lost():
    server = WebMeshServer(port=4270)

    @server.on('/echo')
    def echo(payload, path, client: WebMeshConnection):
        return payload

    server.start(threaded=True)
    server.await_started()

    client = WebMeshClient(port=4270)
    client.start(threaded=True)
    client.await_started()

    server.close()  # Disrupt connection
    time.sleep(20)

    server.start(threaded=True)
    server.await_started()
    client.await_started()

    print(client.call('/id', None))

    Event().wait()
