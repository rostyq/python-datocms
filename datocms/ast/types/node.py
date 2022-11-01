from typing import Literal, TypedDict


__all__ = ["Node", "NodeTypeName"]


NodeTypeName = Literal[
    "span",
    "link",
    "itemLink",
    "inlineItem",
    "heading",
    "list",
    "listItem",
    "code",
    "blockquote",
    "block",
    "thematicBreak",
]


class Node(TypedDict):
    type: NodeTypeName
