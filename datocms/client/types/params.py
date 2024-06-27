from typing import Any, TypedDict, NotRequired

from datocms.types.relationships import Creator, ItemType


__all__ = [
    "Payload",
    "PayloadData",
    "PayloadGraphQL",
    "PayloadUpdate",
    "RelationshipsUpdate",
]


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
