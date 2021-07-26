import asyncio
import logging
from multiprocessing.pool import ThreadPool
from typing import Any

import websockets

from webmesh.message_protocols import AbstractMessageProtocol, SimpleDictProtocol
from webmesh.message_serializers import AbstractMessageSerializer, MessagePackSerializer
from webmesh.utils import blocking_send, blocking_recv
from webmesh.webmesh_component import WebMeshComponent


class WebMeshClient(WebMeshComponent):
    def __init__(self, host: str = '127.0.0.1', port: int = 4269, debug: bool = False,
                 message_serializer: AbstractMessageSerializer = MessagePackSerializer(),
                 message_protocol: AbstractMessageProtocol = SimpleDictProtocol()):
        super().__init__(host, port, message_serializer, message_protocol)

        self.client = None
        self.thread_pool = ThreadPool(processes=1)
        self.logger = logging.getLogger('webmesh.client')

    def _emit(self, target: str, data: Any):
        packed_message = self.message_protocol.pack(target, data)
        serialized_message = self.message_serializer.serialize(packed_message)
        self.logger.debug(f'Sending {data} to {target}...')
        blocking_send(self.client, serialized_message)

    def emit(self, target: str, data: Any):
        return self.thread_pool.apply(self._emit, args=[target, data])

    def _call(self, target: str, data: Any):
        self._emit(target, data)

        serialized_response = blocking_recv(self.client)
        packed_response = self.message_serializer.deserialize(serialized_response)
        data = self.message_protocol.unpack(packed_response)[1]  # Return only the data
        self.logger.debug(f'Received response {data} for {target} request.')

        return data

    def call(self, target: str, data: Any):
        return self.thread_pool.apply(self._call, args=[target, data])

    def call_async(self, target: str, data: Any, callback=lambda result: None):
        return self.thread_pool.apply_async(self._call, args=[target, data], callback=callback)

    async def run(self):
        await super().run()
        async with websockets.connect(f'ws://{self.host}:{self.port}') as client:
            self.client = client
            self.started.set()
            self.logger.info(f'Connected to ws://{self.host}:{self.port}')

            while not self.stop.is_set():
                if client.closed:
                    raise OSError
                else:
                    await asyncio.sleep(1)
            self.logger.info('Disconnected.')
