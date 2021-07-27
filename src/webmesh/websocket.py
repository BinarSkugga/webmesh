import base64
import dataclasses
import hashlib
import socket
import threading
import uuid
from abc import abstractmethod
from multiprocessing.pool import ThreadPool
from typing import Tuple

from wsproto import WSConnection, ConnectionType
from wsproto.events import Request, AcceptConnection, CloseConnection, TextMessage, BytesMessage


@dataclasses.dataclass
class WebSocketPeer:
    id: str
    socket: socket.socket
    connection: WSConnection
    addr: Tuple[str, int]

    def send(self, data):
        encoded = self.connection.send(data)
        self.socket.send(encoded)

    def recv(self, buffer_size: int):
        data = self.socket.recv(buffer_size)
        self.connection.receive_data(data)
        return data

    def close(self):
        self.connection.receive_data(None)
        self.socket.close()


class WebSocketServer:
    def __init__(self, max_threads: int = 5):
        self.close_event = threading.Event()
        self.read_buffer_size = 1024
        self.thread_pool = ThreadPool(processes=max_threads)
        self.clients = {}

    def _client_process(self, new_socket: socket.socket, addr: Tuple[str, int]):
        client = self._on_connect(new_socket, addr)

        data = True
        while data:
            data = client.recv(self.read_buffer_size)
            for event in client.connection.events():
                if isinstance(event, Request):
                    client.send(AcceptConnection())
                elif isinstance(event, CloseConnection):
                    client.send(event.response())
                    data = False
                elif isinstance(event, TextMessage):
                    print(f'received text: {event.data}')
                elif isinstance(event, BytesMessage):
                    print(f'received bytes: {event.data}')
            self._on_message(client, data)

        self._on_disconnect(client)
        client.close()

    def _on_connect(self, sock, addr):
        id = uuid.uuid4().hex
        client = WebSocketPeer(id, sock, WSConnection(ConnectionType.SERVER), addr)
        self.clients[id] = client
        print(f'{client.id} connected')
        return client

    def _on_message(self, client: WebSocketPeer, data: bytes):
        print(f'{client.id} received {data}')
        self.on_message(client, data)

    def _on_disconnect(self, client: WebSocketPeer):
        del self.clients[client.id]
        print(f'{client.id} disconnected')

    def close(self):
        self.close_event.set()

    def _listen(self, host: str, port: int):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((host, port))
        sock.listen()

        while not self.close_event.is_set():
            print('Awaiting new clients...')
            connection, addr = sock.accept()
            self.thread_pool.apply_async(self._client_process, args=[connection, addr])

        sock.close()

    def listen(self, host: str, port: int, non_blocking: bool = True):
        if non_blocking:
            threading.Thread(target=self._listen, daemon=True, args=[host, port]).start()
        else:
            self._listen(host, port)

    @abstractmethod
    def on_connect(self, client: WebSocketPeer):
        pass

    @abstractmethod
    def on_message(self, client: WebSocketPeer, data: bytes):
        pass

    @abstractmethod
    def on_disconnect(self, client: WebSocketPeer):
        pass


ws = WebSocketServer()
ws.listen('0.0.0.0', 4269)

input()  # Press enter to close the socket

ws.close()
