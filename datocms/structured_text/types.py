from typing import Literal, TypedDict, Generic, TypeVar, NotRequired, Type, Union


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
ListItemNodeType = Union[ParagraphType, ListType]


ListStyle = Literal["bulleted", "numbered"]
DefaultMark = Literal[
    "strong", "code", "emphasis", "underline", "strikethrough", "highlight"
]


F = TypeVar("F", bound=DefaultMark, covariant=True, contravariant=True)
T = TypeVar("T", bound=NodeType, covariant=True, contravariant=False)
R = TypeVar("R", bound=RootNodeType, covariant=True, contravariant=False)
B = TypeVar("B")
L = TypeVar("L")


class Node(TypedDict, Generic[T]):
    type: T


class MetaEntry(TypedDict):
    id: str
    value: str


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
    children: list[Span[F]]


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


class Heading(TypedDict):
    type: HeadingType
    level: Literal[1, 2, 3, 4, 5, 6]
    style: NotRequired[str]
    children: list[Node[InlineNodeType]]


class ListItem(TypedDict):
    type: ListItemType
    children: list[Node[ListItemNodeType]]


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
    children: list[Paragraph]
    attribution: NotRequired[str]


class Root(TypedDict, Generic[R]):
    type: Literal["root"]
    children: list[Node[R]]


class Document(TypedDict, Generic[R]):
    schema: Literal["dast"]
    document: Root[R]


class StructuredText(TypedDict, Generic[R, B, L]):
    value: Document[R]
    blocks: NotRequired[list[B]]
    links: NotRequired[list[L]]
