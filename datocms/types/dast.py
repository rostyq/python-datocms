from typing import (
    Literal,
    TypedDict,
    Generic,
    TypeVar,
    NotRequired,
    Union,
    Required,
)


ParagraphType = Literal["paragraph"]
SpanType = Literal["span"]
LinkType = Literal["link"]
ItemLinkType = Literal["itemLink"]
InlineItemType = Literal["inlineItem"]
HeadingType = Literal["heading"]
ListType = Literal["list"]
ListItemType = Literal["listItem"]
CodeType = Literal["code"]
BlockquoteType = Literal["blockquote"]
BlockType = Literal["block"]
ThematicBreakType = Literal["thematicBreak"]


NodeType = Union[
    ParagraphType,
    HeadingType,
    LinkType,
    ItemLinkType,
    InlineItemType,
    BlockType,
    ListType,
    ListItemType,
    BlockquoteType,
    CodeType,
    SpanType,
    ThematicBreakType,
]
RootNodeType = Union[
    ParagraphType,
    HeadingType,
    ListType,
    CodeType,
    BlockquoteType,
    BlockType,
    ThematicBreakType,
]
CustomStyleBlockNodeType = Union[ParagraphType, HeadingType]
InlineNodeType = Union[SpanType, LinkType, ItemLinkType, InlineItemType]
MetaNodeType = Union[LinkType, ItemLinkType]
ListNodeType = Union[ParagraphType, ListType]
ChildNodeType = Union[ListItemType, InlineNodeType]
OptionalNodeType = Union[BlockquoteType, CodeType, HeadingType, LinkType, ListType, ThematicBreakType]
BaseNodeType = Union[BlockType, ParagraphType]


ListStyle = Literal["bulleted", "numbered"]
FormatMark = Literal[
    "strong", "code", "emphasis", "underline", "strikethrough", "highlight"
]
HeaderLevel = Literal[1, 2, 3, 4, 5, 6]


F = TypeVar("F", bound=FormatMark, covariant=True, contravariant=False)
R = TypeVar("R", bound=OptionalNodeType, covariant=True, contravariant=False)
H = TypeVar("H", bound=HeaderLevel, covariant=True, contravariant=False)
B = TypeVar("B")
L = TypeVar("L")


class MetaEntry(TypedDict):
    id: str
    value: str


class InlineNode(TypedDict, Generic[F], total=False):
    type: Required[InlineNodeType]
    item: str
    value: str
    url: str
    marks: list[F]
    meta: list[MetaEntry]
    children: list["Span[F]"]


class ItemNode(TypedDict, Generic[F], total=False):
    type: Required[Union[SpanType, ListNodeType]]
    value: str
    marks: list[F]
    children: list["ChildNode[F]"]


class ChildNode(TypedDict, Generic[F], total=False):
    type: Required[ChildNodeType]
    item: str
    value: str
    url: str
    marks: list[F]
    style: str
    meta: list[MetaEntry]
    children: list[ItemNode[F]]


class ListNode(TypedDict, Generic[F]):
    type: ListNodeType
    style: NotRequired[str]
    children: list[ChildNode[F]]


class RootNode(TypedDict, Generic[R, H, F], total=False):
    type: Required[Union[BaseNodeType, R]]
    item: str
    value: str
    url: str
    attribution: str
    level: H
    style: str
    code: str
    language: str
    highlight: list[int]
    meta: list[MetaEntry]
    children: list[ChildNode[F]]


class ThematicBreak(TypedDict):
    type: ThematicBreakType


class Block(TypedDict):
    type: BlockType
    item: str


class Span(TypedDict, Generic[F]):
    type: SpanType
    value: str
    marks: NotRequired[list[F]]


class Paragraph(TypedDict, Generic[F]):
    type: ParagraphType
    children: list[InlineNode[F]]


class Link(TypedDict, Generic[F]):
    type: LinkType
    url: str
    meta: NotRequired[list[MetaEntry]]
    children: list[Span[F]]


class ItemLink(TypedDict, Generic[F]):
    type: ItemLinkType
    item: str
    meta: NotRequired[MetaEntry]
    children: list[Span[F]]


class InlineItem(TypedDict):
    type: InlineItemType
    item: str


class Heading(TypedDict, Generic[H, F]):
    type: HeadingType
    level: H
    style: NotRequired[str]
    children: list[InlineNode[F]]


class ListItem(TypedDict, Generic[F]):
    type: ListItemType
    children: list[ListNode[F]]


class List(TypedDict, Generic[F]):
    type: ListType
    style: ListStyle
    children: list[ListItem[F]]


class Code(TypedDict):
    type: CodeType
    code: str
    language: NotRequired[str]
    highlight: NotRequired[list[int]]


class Blockquote(TypedDict, Generic[F]):
    type: BlockquoteType
    attribution: NotRequired[str]
    children: list[Paragraph[F]]


class Root(TypedDict, Generic[R, H, F]):
    type: Literal["root"]
    children: list[RootNode[R, H, F]]


class Document(TypedDict, Generic[R, H, F]):
    schema: Literal["dast"]
    document: Root[R, H, F]


class StructuredText(TypedDict, Generic[R, H, F, B, L]):
    value: Document[R, H, F]
    blocks: NotRequired[list[B]]
    links: NotRequired[list[L]]
