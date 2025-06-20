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
    "RootChildType",
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


DastSchemaType = Literal["dast"]
RootNodeType = Literal["root"]
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
RootChildType = Union[
    ParagraphType,
    HeadingType,
    ListType,
    CodeType,
    BlockquoteType,
    BlockType,
    ThematicBreakType,
]
NodeType = Union[
    RootChildType,
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


class BaseNode(TypedDict):
    type: NodeType


class Span(BaseNode):
    type: SpanType
    value: str
    marks: NotRequired[Marks]


class InlineBlock(BaseNode):
    type: InlineBlockType
    item: str


class ItemLink(BaseNode):
    type: ItemLinkType
    item: str
    meta: NotRequired[MetaEntry]
    children: list[Span]


class InlineItem(BaseNode):
    type: InlineItemType
    item: str


class Link(BaseNode):
    type: LinkType
    url: str
    meta: NotRequired[list[MetaEntry]]
    children: list[Span]


InlineNode = Union[Span, Link, ItemLink, InlineItem, InlineBlock]


class Paragraph(BaseNode):
    type: ParagraphType
    style: NotRequired[str]
    children: list[InlineNode]


class Heading(BaseNode):
    type: HeadingType
    level: HeaderLevel
    style: NotRequired[str]
    children: list[InlineNode]


ListNode = Union["List", Paragraph]


class ListItem(BaseNode):
    type: ListItemType
    children: list[ListNode]


class List(BaseNode):
    type: ListType
    style: ListStyle
    children: list[ListItem]


class Code(BaseNode):
    type: CodeType
    code: str
    language: NotRequired[str]
    highlight: NotRequired[list[int]]


class Blockquote(BaseNode):
    type: BlockquoteType
    attribution: NotRequired[str]
    children: list[Paragraph]


class Block(BaseNode):
    type: BlockType
    item: str


class ThematicBreak(BaseNode):
    type: ThematicBreakType


RootNode = Union[Paragraph, Heading, List, Code, Blockquote, Block, ThematicBreak]


class Root(TypedDict):
    type: RootNodeType
    children: list[RootNode]


class Document(TypedDict):
    schema: DastSchemaType
    document: Root
