from typing import TypedDict, Literal, Any


__all__ = [
    "Id",
    "Item",
    "ItemId",
    "ItemTypeId",
    "FieldId",
    "FieldSetId",
    "WorkflowId",
    "CreatorId",
    "CreatorRelationships",
    "ItemTypeRelationships",
    "Relationships",
]


class Id(TypedDict):
    id: str


class ItemId(Id):
    type: Literal["item"]


class ItemTypeId(Id):
    type: Literal["item_type"]


class FieldId(Id):
    type: Literal["field"]


class FieldSetId(Id):
    type: Literal["fieldset"]


class WorkflowId(Id):
    type: Literal["workflow"]


class CreatorId(Id):
    type: Literal["account", "access_token", "user", "sso_user"]


class ItemType(TypedDict):
    data: ItemTypeId


class Creator(TypedDict):
    data: CreatorId


class CreatorRelationships(TypedDict):
    creator: Creator


class ItemTypeRelationships(TypedDict):
    item_type: ItemType


class Item(TypedDict):
    id: str
    type: Literal["item"]
    attributes: dict[str, Any]
    relationships: ItemTypeRelationships
