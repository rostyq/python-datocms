from typing import Literal, TypedDict, NewType

from .relationships import CreatorRelationships, ItemTypeRelationships

__all__ = ["Attributes", "Meta", "Record", "RecordId"]

RecordId = NewType("RecordId", str)


class Attributes(TypedDict):
    created_at: str
    updated_at: str


class Meta(TypedDict):
    created_at: str
    updated_at: str
    published_at: str
    first_published_at: None | str
    publication_scheduled_at: None | str
    unpublishing_scheduled_at: None | str
    status: None | Literal["draft", "updated", "published"]
    is_current_version_valid: None | bool
    is_published_version_valid: None | bool
    current_version: str
    stage: None | str
    is_valid: bool


class Relationships(CreatorRelationships, ItemTypeRelationships):
    pass


RecordTypeName = Literal["item"]


class Record(TypedDict):
    id: RecordId
    type: RecordTypeName
    attributes: Attributes
    meta: Meta
    relationships: Relationships
