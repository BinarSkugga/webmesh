import json
from abc import ABC, abstractmethod
from typing import Any


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
