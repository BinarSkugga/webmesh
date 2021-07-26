# WebMesh
![Deploy](https://github.com/binarskugga/webmesh/actions/workflows/python-publish.yml/badge.svg)

## Tests & Lint
Install nox: `pip install nox`

Execute all the session at the root of the project: `nox`

## Install

Simply execute: `pip install webmesh`


## WebMesh Server
WebMesh's server works like a standard HTTP server. It uses a declarative syntax with decorators defining callbacks on routes. Here's the basic example for a locally accessible echo server:

```python
from webmesh.webmesh_server import WebMeshServer, WebMeshConnection

server = WebMeshServer()

@server.on('/')
def echo(payload, path, client: WebMeshConnection):
    return payload

server.start(threaded=True)
server.await_started()

# Server is ready and running in its own thread

server.close()
```

This is all good and pretty but by default, WebMesh uses [msgpack](https://github.com/msgpack/msgpack-python) and zlib to communicate which makes it hard to manually use. You can change the serialization layer by providing an implementation of the `AbstractMessageSerializer` class. WebMesh provides a simple JSON serializer that you can pass into your server's constructor:

```python
from webmesh.webmesh_server import WebMeshServer
from webmesh.message_serializers import StandardJsonSerializer

server = WebMeshServer(message_serializer=StandardJsonSerializer())
```

## WebMesh Client
WebMesh's client wraps the connection from websockets and allow you to emit and call using both a blocking and non-blocking. This client doesn't execute anything on the main thread. Here's a basic example:

```python
from webmesh.webmesh_client import WebMeshClient

client = WebMeshClient()
client.start(threaded=True)
client.await_started()

# Client is ready and running in its own thread

client.close()
```

WebMesh clients use the same process as the server to serialize and pack messages. You can override how this happens by providing a different implementation of `AbstractMessageSerializer` or `AbstractMessageProtocol`. **Make sure the server and clients use the same Serializer and Protocol or equivalent implementations.**
