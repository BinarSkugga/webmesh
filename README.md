# WebMesh
![Deploy](https://github.com/binarskugga/webmesh/actions/workflows/python-publish.yml/badge.svg)

## Todo before first release
- [ ] Add SSL Support
- [ ] Improve Failure Resilience (retrying connections etc..)
- [ ] Implement a Subscription System
- [ ] Implement a class that regroups a server and multiple clients to each peers (WebMesh(server, *peers) ?)

## Tests & Lint
Install nox: `pip install nox`

Execute all the session at the root of the project: `nox`

## Install

Simply execute: `pip install webmesh`


## WebSocket Implementation
[TODO]


## WebMesh Server
WebMesh's server works like a standard HTTP server. It uses a declarative syntax with decorators defining callbacks on routes. Here's the basic example for a locally accessible echo server:

```python
from typing import Any

from webmesh.websocket.websocket_connection import WebSocketConnection
from webmesh.webmesh_server import WebMeshServer

server = WebMeshServer()

@server.on('/')
def echo(payload: Any, path: str, client: WebSocketConnection):
    return payload

server.listen()
server.await_started()

# Server is ready and running in its own thread

server.close()
```

This is all good and pretty but by default, WebMesh uses [msgpack](https://github.com/msgpack/msgpack-python) and zlib to communicate which makes it hard to manually use. You can change the serialization layer by providing an implementation of the `AbstractMessageSerializer` class. WebMesh provides a simple JSON serializer that you can pass into your server's constructor:

```python
from webmesh.webmesh_server import WebMeshServer
from webmesh.message_serializers import StandardJsonSerializer

server = WebMeshServer(serializer_type=StandardJsonSerializer)
```

**Note that we are using the class and not an instance. This is because the websocket backend uses processes for parallelism. This limits us as to what we can use because it requires to be pickled. By passing the class, we can instantiate the serializer inside the process and have more flexibility.**
