import json
from abc import ABC, abstractmethod
from typing import Any


class AbstractMessageSerializer(ABC):
    @abstractmethod
    def to_str(self, obj: Any) -> str:
        pass

    @abstractmethod
    def from_str(self, data: str) -> Any:
        pass


class StandardJsonSerializer(AbstractMessageSerializer):
    def to_str(self, obj: Any) -> str:
        return json.dumps(obj)

    def from_str(self, data: str) -> Any:
        return json.loads(data)
