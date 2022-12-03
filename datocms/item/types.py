from typing import Any, TypedDict, Literal
from ..types.relationships import ItemTypeRelationships


__all__ = ["Item"]


class Item(TypedDict):
    id: str
    type: Literal["item"]
    attributes: dict[str, Any]
    relationships: ItemTypeRelationships
