# WebMesh
![Deploy](https://github.com/binarskugga/webmesh/actions/workflows/python-publish.yml/badge.svg)

## Tests & Lint
Install nox: `pip install nox`

Execute all the session at the root of the project: `nox`

## Install

Simply execute: `pip install webmesh`


## How to use
WebMesh's server works like a standard HTTP server. It uses a declarative syntax with decorators defining callbacks on routes. Here's the basic example for a locally accessible echo server:

```python
from webmesh.webmesh_server import WebMeshServer, WebMeshConnection

server = WebMeshServer()

@server.on('/')
def echo(payload, path, client: WebMeshConnection):
    return payload

server.start()
```

This is all good and pretty but by default, WebMesh uses [msgpack](https://github.com/msgpack/msgpack-python) and zlib to communicate which makes it hard to manually use. You can change the serialization layer by providing an implementation of the `AbstractMessageSerializer` class. WebMesh provides a simple JSON serializer that you can pass into your server's constructor:

```python
from webmesh.webmesh_server import WebMeshServer
from webmesh.message_serializers import StandardJsonSerializer

server = WebMeshServer(message_serializer=StandardJsonSerializer())
```
