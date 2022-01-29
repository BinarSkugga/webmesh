from abc import ABC, abstractmethod
from typing import Tuple, Any, Optional


class AbstractMessageProtocol(ABC):
    @abstractmethod
    def unpack(self, message: Any) -> Tuple[str, Any]:
        pass

    @abstractmethod
    def pack(self, target: Optional[str], message: Any) -> Any:
        pass


class SimpleDictProtocol(AbstractMessageProtocol):
    def unpack(self, message: Any) -> Tuple[str, Any]:
        return message['target'], message['data'] if 'data' in message else None

    def pack(self, target: Optional[str], message: Any) -> Any:
        return {'target': target, 'data': message}
