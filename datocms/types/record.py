from typing import Literal, TypedDict

from .relationships import CreatorRelationships, ItemTypeRelationships


__all__ = ["Attributes", "Meta", "Record"]


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


class Record(TypedDict):
    id: str
    type: Literal["item"]
    attributes: Attributes
    meta: Meta
    relationships: Relationships
