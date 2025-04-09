from typing import Any, TypedDict, NotRequired, Literal

from .relationships import Creator, ItemType


__all__ = [
    "Version",
    "AnyVersion",
    "TagType",
    "Result",
    "Payload",
    "PayloadData",
    "PayloadGraphQL",
    "PayloadUpdate",
    "RelationshipsUpdate",
    "Result",
    "ArrayResult",
    "Meta",
    "PageParams",
    "FilterParams",
    "GraphqlParams",
    "PageParams",
    "FilterParams",
    "RecordsParams",
    "GraphqlResult",
    "GraphqlError",
    "ErrorLocation",
]

Version = Literal["published", "current"]
AnyVersion = Literal[Version, "published-or-current"]
TagType = Literal["manual", "smart"]


class RelationshipsUpdate(TypedDict, total=False):
    creator: Creator
    item: ItemType


class PayloadData(TypedDict):
    type: str
    attributes: dict[str]


class PayloadUpdate(TypedDict):
    id: str
    type: str
    relationships: NotRequired[RelationshipsUpdate]


class Payload(TypedDict):
    data: PayloadData


class PayloadGraphQL(TypedDict):
    query: str
    attributes: NotRequired[dict[str, Any]]
    variables: NotRequired[dict[str, Any]]


class Result(TypedDict):
    data: dict[str, Any]


class Meta(TypedDict):
    total_count: int


class ArrayResult(TypedDict):
    data: list[Any]
    meta: Meta


class ErrorLocation(TypedDict):
    line: int
    column: int


class GraphqlError(TypedDict):
    message: str
    locations: NotRequired[list[ErrorLocation]]
    path: list[str]


class GraphqlResult(TypedDict):
    data: Any
    errors: NotRequired[list[dict[str, Any]]]
