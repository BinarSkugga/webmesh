import json
from abc import ABC, abstractmethod
from typing import Any
import zlib

import msgpack


class AbstractMessageSerializer(ABC):
    @abstractmethod
    def serialize(self, obj: Any) -> str:
        pass

    @abstractmethod
    def deserialize(self, data: str) -> Any:
        pass


class StandardJsonSerializer(AbstractMessageSerializer):
    def serialize(self, obj: Any) -> str:
        return json.dumps(obj)

    def deserialize(self, data: str) -> Any:
        return json.loads(data)


class MessagePackSerializer(AbstractMessageSerializer):
    def __init__(self, compressor=zlib):
        self.compressor = compressor

    def serialize(self, obj: Any) -> str:
        msg_bytes = msgpack.dumps(obj)
        if self.compressor is not None:
            msg_bytes = self.compressor.compress(msg_bytes)
        return msg_bytes.hex()

    def deserialize(self, data: str) -> Any:
        bytes_data = bytes.fromhex(data)
        if self.compressor is not None:
            bytes_data = self.compressor.decompress(bytes_data)
        return msgpack.loads(bytes_data)


print(MessagePackSerializer().serialize({'path': '/id'}))
print(MessagePackSerializer().deserialize('789cbba9606e619e966a6c996698946a6c629a929294666660686c916669696c69696a980400b48509a8'))
