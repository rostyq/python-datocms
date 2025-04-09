from typing import Literal, TypedDict, NewType, Required, NotRequired

from . import DataField
from .relationships import FieldId, FieldSetId, ItemId, WorkflowId


__all__ = [
    "ModelId",
    "Model",
    "Attributes",
    "Id",
    "FieldId",
    "FieldSetId",
    "WorkflowId",
    "ItemId",
    "Fields",
    "FieldSets",
    "Relationships",
]

ModelId = NewType("ModelId", str)


class Attributes(TypedDict):
    name: str
    api_key: str
    singleton: bool
    sortable: bool
    modular_block: bool
    tree: bool
    ordering_direction: NotRequired[Literal["asc", "desc"]]
    ordering_meta: NotRequired[
        Literal["created_at", "updated_at", "first_published_at", "published_at"]
    ]
    draft_mode_active: bool
    all_locales_required: bool
    collection_appearance: Literal["compact", "table"]
    has_singleton_item: bool
    hint: NotRequired[str]


class Relationships(TypedDict, total=False):
    singleton_item: DataField[ItemId]
    fields: Required[DataField[list[FieldId]]]
    field_sets: Required[DataField[list[FieldSetId]]]
    title_field: DataField[FieldId]
    image_preview_field: DataField[FieldId]
    excerpt_field: DataField[FieldId]
    ordering_field: DataField[FieldId]
    workflow: DataField[WorkflowId]


ModelTypeName = Literal["item_type"]


class Model(TypedDict):
    id: ModelId
    type: ModelTypeName
    attributes: Attributes
    relationships: Relationships
