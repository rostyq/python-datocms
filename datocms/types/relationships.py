from typing import TypedDict, Literal, Any


__all__ = [
    "Id",
    "Item",
    "ItemId",
    "ItemType",
    "ItemTypeId",
    "FieldId",
    "FieldSetId",
    "WorkflowId",
    "Creator",
    "CreatorId",
    "CreatorRelationships",
    "ItemTypeRelationships",
    "UploadCollectionId",
    "UploadCollectionRelationship",
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


class UploadCollectionId(Id):
    type: Literal["upload_collection"]


class ItemType(TypedDict):
    data: ItemTypeId


class Creator(TypedDict):
    data: CreatorId


class UploadCollectionRelationship(TypedDict):
    data: UploadCollectionId


class CreatorRelationships(TypedDict):
    creator: Creator


class ItemTypeRelationships(TypedDict):
    item_type: ItemType


class Item(TypedDict):
    id: str
    type: Literal["item"]
    attributes: dict[str, Any]
    relationships: ItemTypeRelationships


class UploadCollection(TypedDict):
    id: str
    type: Literal["upload_collection"]
    attributes: dict[str, Any]
