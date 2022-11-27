from typing import Literal, TypedDict, Generic, TypeVar, NotRequired, Type

from ..record.types import Record, RecordId


HeadingTypeName = Literal["heading"]


class Heading(TypedDict):
    type: HeadingTypeName
    level: Literal[1, 2, 3, 4, 5, 6]
    style: NotRequired[str]
    children: list[Type["InlineNode"]]


ListStyle = Literal["bulleted", "numbered"]
ListTypeName = Literal["list"]


class List(TypedDict):
    type: ListTypeName
    style: ListStyle
    children: list[Type["ListItem"]]


CodeTypeName = Literal["code"]


class Code(TypedDict):
    type: CodeTypeName
    code: str
    language: NotRequired[str]
    highlight: NotRequired[list[int]]


DefaultMark = Literal[
    "strong", "code", "emphasis", "underline", "strikethrough", "highlight"
]


Sm = TypeVar("Sm", bound=DefaultMark)
SpanTypeName = Literal["span"]


class Span(TypedDict, Generic[Sm]):
    type: SpanTypeName
    value: str
    marks: NotRequired[list[Sm]]


class MetaEntry(TypedDict):
    id: str
    value: str


LinkTypeName = Literal["link"]


class Link(TypedDict):
    type: LinkTypeName
    url: str
    meta: NotRequired[list[MetaEntry]]
    children: list[Span]


ItemLinkTypeName = "itemLink"


class ItemLink(TypedDict):
    type: ItemLinkTypeName
    item: RecordId
    meta: NotRequired[MetaEntry]
    children: list[Span]


NodeWithMeta = Link | ItemLink


InlineItemTypeName = "inlineItem"


class InlineItem(TypedDict):
    type: InlineItemTypeName
    item: RecordId


InlineNode = Span | Link | ItemLink | InlineItem


ParagraphTypeName = Literal["paragraph"]


class Paragraph(TypedDict):
    type: ParagraphTypeName
    children: list[Span]


BlockNodeWithCustomStyle = Paragraph | Heading

BlockNodeTypeWithCustomStyle = ParagraphTypeName | HeadingTypeName


ListItemTypeName = Literal["listItem"]


class ListItem(TypedDict):
    type: ListItemTypeName
    children: list[Paragraph | List]


BlockquoteTypeName = Literal["blockquote"]


class Blockquote(TypedDict):
    type: BlockquoteTypeName
    children: list[Paragraph]
    attribution: NotRequired[str]


BlockTypeName = Literal["block"]
Rb = TypeVar("Rb", RecordId, Record, covariant=True)


class Block(TypedDict, Generic[Rb]):
    type: BlockTypeName
    item: Rb


ThematicBreakTypeName = Literal["thematicBreak"]


class ThematicBreak(TypedDict):
    type: ThematicBreakTypeName


RootTypeName = Literal["root"]


class Root(TypedDict):
    type: RootTypeName
    children: list[
        Paragraph | Heading | List | Code | Blockquote | Block | ThematicBreak
    ]


NodeTypeName = (
    ParagraphTypeName
    | HeadingTypeName
    | LinkTypeName
    | ItemLinkTypeName
    | InlineItemTypeName
    | BlockTypeName
    | ListTypeName
    | ListItemTypeName
    | BlockquoteTypeName
    | CodeTypeName
    | RootTypeName
    | SpanTypeName
    | ThematicBreakTypeName
)

BlockNode = (
    Root
    | Paragraph
    | Heading
    | Block
    | List
    | ListItem
    | Blockquote
    | Code
    | ThematicBreak
)

Node = BlockNode | InlineNode


class Document(TypedDict):
    schema: Literal["dast"]
    document: Root


R1 = TypeVar("R1", bound=Record)
R2 = TypeVar("R2", bound=Record)


class StructuredText(TypedDict, Generic[R1, R2]):
    value: Document
    blocks: NotRequired[list[R1]]
    links: NotRequired[list[R2]]
