from typing import TypedDict, Literal, Any, NewType, NotRequired

from datocms.types.locale import Localized
from .relationships import CreatorRelationships, UploadCollectionRelationship


__all__ = [
    "Color",
    "FocalPoint",
    "Metadata",
    "Attributes",
    "Upload",
    "UploadId",
    "UploadTypeName",
    "UploadTagId",
    "UploadAttributes",
    "UploadTag",
    "UploadPermission",
    "UploadPermissionAttributes",
    "ManualUploadTag",
    "SmartUploadTag",
    "Attributes",
    "UploadCollection",
    "UploadCollectionId",
    "UploadCollectionAttributes",
    "UploadCollectionRelationships",
    "UploadRelationships",
]

UploadId = NewType("UploadId", str)


class Color(TypedDict):
    red: int
    green: int
    blue: int
    alpha: int


class FocalPoint(TypedDict):
    x: float
    y: float


class Metadata(TypedDict):
    alt: str | None
    title: str | None
    custom_data: dict[str, str]
    focal_point: FocalPoint | None


class UploadAttributes(TypedDict):
    size: int
    width: None | int
    height: None | int
    path: str
    basename: str
    filename: str
    url: str
    format: str | None
    author: str | None
    copyright: str | None
    notes: str | None
    md5: str
    duration: int | None
    frame_rate: int | None
    blurhash: str | None
    mux_playback_id: str | None
    mux_mp4_highest_res: Literal["high", "medium", "low"] | None
    default_field_metadata: Localized[Metadata]
    is_image: bool
    created_at: None | str
    updated_at: None | str
    mime_type: None | str
    tags: list[str]
    smart_tags: list[str]
    exif_info: dict[str, Any]
    colors: list[Color]


# Upload Collection types
UploadCollectionId = NewType("UploadCollectionId", str)


class UploadCollectionAttributes(TypedDict):
    label: str
    position: NotRequired[int]


class UploadCollectionData(TypedDict):
    id: UploadCollectionId
    type: Literal["upload_collection"]


class UploadCollectionReference(TypedDict):
    data: UploadCollectionData | None


# Upload relationships with upload collection
class UploadRelationships(CreatorRelationships):
    upload_collection: UploadCollectionReference


UploadTypeName = Literal["upload"]


class Upload(TypedDict):
    id: UploadId
    type: UploadTypeName
    attributes: UploadAttributes
    relationships: UploadRelationships


UploadTagId = NewType("UploadTagId", str)


class Attributes(TypedDict):
    name: str


class UploadTag(TypedDict):
    id: UploadTagId
    type: Literal["upload_tag", "upload_smart_tag"]
    attributes: Attributes


class ManualUploadTag(UploadTag):
    type: Literal["upload_tag"]


class SmartUploadTag(UploadTag):
    type: Literal["upload_smart_tag"]


class UploadPermissionAttributes(TypedDict):
    url: str
    request_headers: dict[str, str]


class UploadPermission(TypedDict):
    id: str
    type: Literal["upload_request"]
    attributes: UploadPermissionAttributes


class UploadCollectionRelationships(TypedDict, total=False):
    parent: UploadCollectionReference
    children: list[UploadCollectionData]


class UploadCollection(TypedDict):
    id: UploadCollectionId
    type: Literal["upload_collection"]
    attributes: UploadCollectionAttributes
    relationships: NotRequired[UploadCollectionRelationships]
