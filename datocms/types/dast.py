from typing import Literal, TypedDict, NotRequired, Union


__all__ = [
    "Mark",
    "Marks",
    "HeaderLevel",
    "MetaEntry",
    "NodeType",
    "Document",
    "DefaultMark",
    "InlineNode",
    "Root",
    "RootNode",
    "RootNodeType",
    "Paragraph",
    "ParagraphType",
    "Span",
    "SpanType",
    "Link",
    "LinkType",
    "ItemLink",
    "ItemLinkType",
    "InlineItem",
    "InlineItemType",
    "InlineBlock",
    "InlineBlockType",
    "Heading",
    "HeadingType",
    "List",
    "ListStyle",
    "ListNodeType",
    "ListType",
    "ListItem",
    "ListItemType",
    "Code",
    "CodeType",
    "Blockquote",
    "BlockquoteType",
    "Block",
    "BlockType",
    "ThematicBreak",
    "ThematicBreakType",
]


ParagraphType = Literal["paragraph"]
SpanType = Literal["span"]
LinkType = Literal["link"]
ItemLinkType = Literal["itemLink"]
InlineItemType = Literal["inlineItem"]
InlineBlockType = Literal["inlineBlock"]
HeadingType = Literal["heading"]
ListType = Literal["list"]
ListItemType = Literal["listItem"]
CodeType = Literal["code"]
BlockquoteType = Literal["blockquote"]
BlockType = Literal["block"]
ThematicBreakType = Literal["thematicBreak"]
RootNodeType = Union[
    ParagraphType,
    HeadingType,
    ListType,
    CodeType,
    BlockquoteType,
    BlockType,
    ThematicBreakType,
]
NodeType = Union[
    RootNodeType,
    LinkType,
    ItemLinkType,
    InlineItemType,
    ListItemType,
    SpanType,
]
ListNodeType = Union[ParagraphType, ListType]

ListStyle = Literal["bulleted", "numbered"]
DefaultMark = Literal[
    "strong", "code", "emphasis", "underline", "strikethrough", "highlight"
]
HeaderLevel = Literal[1, 2, 3, 4, 5, 6]

Mark = Union[DefaultMark, str]
Marks = list[Mark]


class MetaEntry(TypedDict):
    id: str
    value: str


class Span(TypedDict):
    type: SpanType
    value: str
    marks: NotRequired[Marks]


class InlineBlock(TypedDict):
    type: InlineBlockType
    item: str


class ItemLink(TypedDict):
    type: ItemLinkType
    item: str
    meta: NotRequired[MetaEntry]
    children: list[Span]


class InlineItem(TypedDict):
    type: InlineItemType
    item: str


class Link(TypedDict):
    type: LinkType
    url: str
    meta: NotRequired[list[MetaEntry]]
    children: list[Span]


InlineNode = Union[Span, Link, ItemLink, InlineItem, InlineBlock]


class Paragraph(TypedDict):
    type: ParagraphType
    style: NotRequired[str]
    children: list[InlineNode]


class Heading(TypedDict):
    type: HeadingType
    level: HeaderLevel
    style: NotRequired[str]
    children: list[InlineNode]


ListNode = Union["List", Paragraph]


class ListItem(TypedDict):
    type: ListItemType
    children: list[ListNode]


class List(TypedDict):
    type: ListType
    style: ListStyle
    children: list[ListItem]


class Code(TypedDict):
    type: CodeType
    code: str
    language: NotRequired[str]
    highlight: NotRequired[list[int]]


class Blockquote(TypedDict):
    type: BlockquoteType
    attribution: NotRequired[str]
    children: list[Paragraph]


class Block(TypedDict):
    type: BlockType
    item: str


class ThematicBreak(TypedDict):
    type: ThematicBreakType


RootNode = Union[Paragraph, Heading, List, Code, Blockquote, Block, ThematicBreak]


class Root(TypedDict):
    type: Literal["root"]
    children: list[RootNode]


class Document(TypedDict):
    schema: Literal["dast"]
    document: Root
