from typing import Any

import websockets

from webmesh.message_protocols import AbstractMessageProtocol, SimpleDictProtocol
from webmesh.message_serializers import AbstractMessageSerializer, MessagePackSerializer
from webmesh.utils import sync_send, sync_recv
from webmesh.webmesh_component import WebMeshComponent


class WebMeshClient(WebMeshComponent):
    def __init__(self, host: str = '127.0.0.1', port: int = 4269,
                 debug: bool = False,
                 message_serializer: AbstractMessageSerializer = MessagePackSerializer(),
                 message_protocol: AbstractMessageProtocol = SimpleDictProtocol()):
        super().__init__()

        self.socket = None
        self.stop = None
        self.host = host
        self.port = port
        self.message_serializer = message_serializer
        self.message_protocol = message_protocol
        self.logger = None

    def emit(self, target: str, data: Any):
        packed_message = self.message_protocol.pack(target, data)
        serialized_message = self.message_serializer.serialize(packed_message)
        sync_send(self.socket, serialized_message)

    def call(self, target: str, data: Any):
        packed_message = self.message_protocol.pack(target, data)
        serialized_message = self.message_serializer.serialize(packed_message)
        sync_send(self.socket, serialized_message)

        serialized_response = sync_recv(self.socket)
        packed_response = self.message_serializer.deserialize(serialized_response)
        return self.message_protocol.unpack(packed_response)[1]  # Return only the data

    async def run(self):
        await super().run()
        async with websockets.connect(f'ws://{self.host}:{self.port}') as socket:
            self.socket = socket
            self.started.set()
            await self.stop.wait()
