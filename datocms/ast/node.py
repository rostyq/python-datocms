from abc import ABC, abstractclassmethod
from typing import Generic
from typing_extensions import TypeVar, Self

from . import types

from .node_type import NodeType

D = TypeVar("D", bound=types.Node)


class Node(ABC, Generic[D]):
    type: NodeType

    @abstractclassmethod
    def from_dict(cls, data: D) -> Self:
        return cls(type=NodeType.from_dict(data))