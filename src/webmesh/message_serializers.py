import json
from abc import ABC, abstractmethod
from typing import Any

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
    def serialize(self, obj: Any) -> str:
        msg_bytes = msgpack.dumps(obj)
        return msg_bytes.hex()

    def deserialize(self, data: str) -> Any:
        bytes_data = bytes.fromhex(data)
        return msgpack.loads(bytes_data)
