import logging
import socket
import threading
import traceback
import uuid
from abc import abstractmethod, ABC
from io import StringIO, BytesIO
from typing import Union, Any, Optional, Tuple

from wsproto import WSConnection, ConnectionType
from wsproto.events import RejectData, BytesMessage, TextMessage, CloseConnection, AcceptConnection, Request, Ping

from webmesh.message_protocols import SimpleDictProtocol
from webmesh.message_serializers import StandardJsonSerializer, AbstractMessageSerializer


class AbstractWebSocketConnection(ABC):
    def __init__(self, connection: Tuple[socket.socket, tuple],
                 serializer: AbstractMessageSerializer = StandardJsonSerializer(SimpleDictProtocol()),
                 connection_type: ConnectionType = ConnectionType.SERVER):
        self.id: str = uuid.uuid4().hex
        self.connection: WSConnection = WSConnection(connection_type)

        self.socket: socket.socket = connection[0]
        self.address: tuple = connection[1]
        self.read_buffer_size = 1024
        self.timeout = 1

        self.serializer = serializer
        self.logger: logging.Logger = logging.getLogger(f'webmesh.{self.id}')

        self.stop_event = threading.Event()

    def send(self, target: Optional[str], obj: Any):
        if target is not None:
            obj = self.serializer.serialize(target, obj)
        encoded = self.connection.send(obj)
        self.socket.send(encoded)

    def recv(self, buffer_size: int):
        data = self.socket.recv(buffer_size)
        self.connection.receive_data(data)
        return data

    def close(self):
        self.stop_event.set()
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    @abstractmethod
    def on_connect(self):
        pass

    @abstractmethod
    def on_disconnect(self):
        pass

    @abstractmethod
    def on_message(self, target: str, message: Any):
        pass

    def listen(self):
        if self.stop_event.is_set():
            self.stop_event = threading.Event()

        self.socket.settimeout(self.timeout)
        self.socket.setblocking(True)

        text_buffer = StringIO()
        bytes_buffer = BytesIO()

        self.on_connect()
        data = True
        while data is not None and not self.stop_event.is_set():
            data = self._handle(self.read_buffer_size, text_buffer, bytes_buffer)
            if isinstance(data, (str, bytes)):
                try:
                    target, unpacked = self.serializer.deserialize(data)
                except:
                    self.logger.info(f'Couldn\'t deserialize data: {data}')
                    continue

                response = self.on_message(target, unpacked)

                if response is not None:
                    packed = self.serializer.serialize(target, response)
                    if isinstance(data, str):
                        self.send(target, TextMessage(data=packed))
                    elif isinstance(data, bytes):
                        self.send(target, BytesMessage(data=packed))
            elif isinstance(data, bool) and not data:
                self.close()
        self.on_disconnect()

        return self.id

    def _handle(self, read_buffer_size: int, text_buffer: StringIO, bytes_buffer: BytesIO) -> Union[bool, str, bytes]:
        try:
            self.recv(read_buffer_size)
            for event in self.connection.events():
                if isinstance(event, Ping):
                    self.send(None, event.response())
                elif isinstance(event, Request):
                    self.send(None, AcceptConnection())
                elif isinstance(event, CloseConnection):
                    self.send(None, event.response())
                    return False
                elif isinstance(event, TextMessage):
                    text_buffer.write(event.data)
                    if event.message_finished:
                        message = text_buffer.getvalue()
                        text_buffer.seek(0)
                        return message
                elif isinstance(event, BytesMessage):
                    bytes_buffer.write(event.data)
                    if event.message_finished:
                        message = bytes_buffer.getvalue()
                        bytes_buffer.seek(0)
                        return message
                else:
                    self.send(None, RejectData(b'Unsupported'))
        except socket.timeout:
            pass
        except Exception:
            traceback.print_exc()
            return False
        return True
