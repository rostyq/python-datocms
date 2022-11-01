from __future__ import annotations

from typing import Literal, Type
from typing_extensions import NotRequired, TypedDict

from .node import Node


__all__ = [
    "SpanMarks",
    "Span",
    "Meta",
    "LinkGeneric",
    "Link",
    "ItemLink",
    "InlineItem",
    "Paragraph",
    "Heading",
    "ListStyle",
    "List",
    "ListItemChild",
    "ListItem",
    "Code",
    "Block",
    "BlockQuote",
    "ThematicBreak",
    "RootChild",
    "Root",
]


SpanMarks = Literal[
    "strong", "code", "emphasis", "underline", "strikethrough", "highlight"
]


class Span(Node):
    type: Literal["span"]
    value: str
    marks: NotRequired[SpanMarks]


class Meta(TypedDict):
    id: str
    value: str


class LinkGeneric(Node):
    type: Literal["link", "itemLink"]
    children: list[Span]
    meta: list[Meta]


class Link(LinkGeneric):
    type: Literal["link"]
    url: str


class ItemLink(LinkGeneric):
    type: Literal["itemLink"]
    item: str


class InlineItem(Node):
    type: Literal["inlineItem"]
    item: str


class Paragraph(Node):
    type: Literal["paragraph"]
    children: list[Span]


HeadingChild = Span | Link | ItemLink | InlineItem


class Heading(Node):
    type: Literal["heading"]
    level: int
    style: NotRequired[str]
    children: list[HeadingChild]


ListStyle = Literal["numbered", "bulleted"]


class List(Node):
    type: Literal["list"]
    style: ListStyle
    children: list[Type["ListItem"]]


ListItemChild = Paragraph | List


class ListItem(Node):
    type: Literal["listItem"]
    children: list[ListItemChild]


class Code(Node):
    type: Literal["code"]
    code: str
    language: NotRequired[str]
    highlight: NotRequired[list[int]]


class BlockQuote(Node):
    type: Literal["blockquote"]
    children: list[Paragraph]
    attribution: NotRequired[str]


class Block(Node):
    type: Literal["block"]
    item: str | dict


class ThematicBreak(Node):
    type: Literal["thematicBreak"]


RootChild = Paragraph | Heading | List | Code | BlockQuote | Block | ThematicBreak


class Root(Node):
    type: Literal["root"]
    children: list[RootChild]
