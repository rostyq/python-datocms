from enum import Enum, global_enum
from typing import Generic, Self, TypeVar, Protocol
from functools import wraps

from .types.dast import NodeType, RootNode as _Node


__all__ = [
    "Node",
    "ROOT",
    "PARAGRAPH",
    "SPAN",
    "LINK",
    "ITEM_LINK",
    "INLINE_ITEM",
    "HEADING",
    "LIST",
    "LIST_ITEM",
    "CODE",
    "BLOCKQUOTE",
    "BLOCK",
    "THEMATIC_BREAK",
    "NodeHandlerType",
]


T = TypeVar("T", bound=_Node)
A = TypeVar("A")
K = TypeVar("K")
R = TypeVar("R")


class NodeHandlerType(Protocol, Generic[T, A, K, R]):
    def __call__(self, node: T, *args: A, **kwargs: K) -> R:
        ...


H = TypeVar("H", bound=NodeHandlerType)


@global_enum
class Node(Enum):
    ROOT = "root"
    PARAGRAPH = "paragraph"
    SPAN = "span"
    LINK = "link"
    ITEM_LINK = "itemLink"
    INLINE_ITEM = "inlineItem"
    HEADING = "heading"
    LIST = "list"
    LIST_ITEM = "listItem"
    CODE = "code"
    BLOCKQUOTE = "blockquote"
    BLOCK = "block"
    THEMATIC_BREAK = "thematicBreak"

    @classmethod
    def get_typename(cls, node: T):
        try:
            name = node["type"]
            assert name in cls._member_names_
            return name
        except KeyError:
            raise KeyError("Passed node object has no `type` value.")
        except AssertionError:
            raise ValueError("Passed dict isn't a node.")

    @classmethod
    def from_dict(cls, data: T) -> Self:
        return cls._value2member_map_[cls.get_typename(data)]

    @classmethod
    def from_str(cls, name: NodeType) -> Self:
        try:
            return cls._value2member_map_[name]
        except KeyError:
            raise KeyError(f"`{name}` is not a node type name.")

    def check(self, node: T) -> T:
        assert (
            node["type"] == self.value
        ), f"Wrong node type: passed `{node['type']}` but needs `{self.value}`."
        return node

    def ensure(self, func: H) -> H:
        @wraps(func)
        def wrapper(node: T, *args, **kwargs):
            return func(self.check(node), *args, **kwargs)

        return wrapper
