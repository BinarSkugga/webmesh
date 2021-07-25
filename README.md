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
