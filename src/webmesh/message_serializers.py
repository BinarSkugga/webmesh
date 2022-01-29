import json
import zlib
from abc import ABC, abstractmethod
from typing import Any, Tuple, Union

import msgpack

from src.webmesh.message_protocols import AbstractMessageProtocol


class AbstractMessageSerializer(ABC):
    def __init__(self, protocol: AbstractMessageProtocol):
        self.protocol = protocol

    @abstractmethod
    def serialize(self, target: str, obj: Any) -> Union[bytes, str]:
        pass

    @abstractmethod
    def deserialize(self, data: Union[bytes, str]) -> Tuple[str, Any]:
        pass


class StandardJsonSerializer(AbstractMessageSerializer):
    def serialize(self, target: str, obj: Any) -> str:
        packed = self.protocol.pack(target, obj)
        return json.dumps(packed)

    def deserialize(self, data: Union[bytes, str]) -> Tuple[str, Any]:
        if isinstance(data, bytes):
            data = data.decode('utf-8')

        json_data = json.loads(data)
        return self.protocol.unpack(json_data)


class MessagePackSerializer(AbstractMessageSerializer):
    def serialize(self, target: str, obj: Any) -> bytes:
        packed = self.protocol.pack(target, obj)
        msg_bytes = msgpack.dumps(packed)
        msg_bytes = zlib.compress(msg_bytes)
        return msg_bytes

    def deserialize(self, data: Union[bytes, str]) -> Tuple[str, Any]:
        if isinstance(data, str):
            data = bytes.fromhex(data)

        decompressed = zlib.decompress(data)
        msg_data = msgpack.loads(decompressed)
        return self.protocol.unpack(msg_data)
