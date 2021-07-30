import logging
from time import sleep

from webmesh.message_protocols import SimpleDictProtocol, AbstractMessageProtocol
from webmesh.message_serializers import AbstractMessageSerializer, MessagePackSerializer
from webmesh.websocket.websocket_client import WebSocketClient
from webmesh.websocket.websocket_connection import WebSocketConnection


class WebMeshClient(WebSocketClient):
    def __init__(self, serializer: AbstractMessageSerializer = MessagePackSerializer(),
                 protocol: AbstractMessageProtocol = SimpleDictProtocol()):
        super().__init__(serializer, protocol)

    def on_connect(self, ws: WebSocketConnection):
        self.logger.info('Connected')

    def on_disconnect(self, ws: WebSocketConnection):
        self.logger.info('Disconnected')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s, %(name)s, %(asctime)s]'
                                                        '[%(threadName)s]'
                                                        '[%(filename)s:%(funcName)s:%(lineno)d]:'
                                                        ' %(message)s')

    client = WebMeshClient()
    client.connect('127.0.0.1', 4269)
    client.await_connected()

    while not client.disconnect_event.is_set():
        if client.connect_event.is_set():
            client.emit('/test', 'ping')
        sleep(1)
