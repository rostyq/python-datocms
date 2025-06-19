from enum import Enum, global_enum
from typing import Self, TypeVar, ParamSpec, Callable, overload, TYPE_CHECKING, Literal
from functools import wraps

from .types.dast import NodeType, RootNode as _Node


__all__ = [
    "Node",
    "ROOT",
    "PARAGRAPH",  # type: ignore
    "SPAN",  # type: ignore
    "LINK",  # type: ignore
    "ITEM_LINK",  # type: ignore
    "INLINE_ITEM",  # type: ignore
    "HEADING",  # type: ignore
    "LIST",  # type: ignore
    "LIST_ITEM",  # type: ignore
    "CODE",  # type: ignore
    "BLOCKQUOTE",  # type: ignore
    "BLOCK",  # type: ignore
    "THEMATIC_BREAK",  # type: ignore
]


R = TypeVar("R")
P = ParamSpec("P")


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
    def get_typename(cls, node: _Node):
        name = node["type"]
        if name not in cls._member_names_:
            raise ValueError(f"Unknown node type: {name}")
        return name

    @classmethod
    def from_dict(cls, data: _Node) -> Self:
        return cls._value2member_map_[cls.get_typename(data)]  # type: ignore

    @classmethod
    def from_str(cls, name: NodeType) -> Self:
        try:
            return cls._value2member_map_[name]  # type: ignore
        except KeyError:
            raise KeyError(f"`{name}` is not a node type name.")

    def check(self, node: _Node) -> _Node:
        if node["type"] != self.value:
            raise TypeError(f"Expected node type '{self.value}', got '{node['type']}'.")
        return node
    
    @overload
    def ensure(self, func: Callable[[_Node], R]) -> Callable[[_Node], R]: ...
    
    @overload  
    def ensure(self, func: Callable[P, R]) -> Callable[P, R]: ...

    def ensure(self, func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(node: _Node, *args: P.args, **kwargs: P.kwargs) -> R:
            return func(self.check(node), *args, **kwargs)

        return wrapper


if TYPE_CHECKING:
    ROOT: Literal[Node.ROOT]
    PARAGRAPH: Literal[Node.PARAGRAPH]
    SPAN: Literal[Node.SPAN]
    LINK: Literal[Node.LINK]
    ITEM_LINK: Literal[Node.ITEM_LINK]
    INLINE_ITEM: Literal[Node.INLINE_ITEM]
    HEADING: Literal[Node.HEADING]
    LIST: Literal[Node.LIST]
    LIST_ITEM: Literal[Node.LIST_ITEM]
    CODE: Literal[Node.CODE]
    BLOCKQUOTE: Literal[Node.BLOCKQUOTE]
    BLOCK: Literal[Node.BLOCK]
    THEMATIC_BREAK: Literal[Node.THEMATIC_BREAK]
