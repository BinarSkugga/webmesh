from abc import ABC, abstractmethod
from typing import Tuple, Any


class AbstractMessageProtocol(ABC):
    @abstractmethod
    def unpack(self, message: Any) -> Tuple[str, Any]:
        pass

    @abstractmethod
    def pack(self, message: Any) -> Any:
        pass


class SimpleDictProtocol(AbstractMessageProtocol):
    def unpack(self, message: Any) -> Tuple[str, Any]:
        return message['path'], message['data'] if 'data' in message else None

    def pack(self, message: Any) -> Any:
        return message
