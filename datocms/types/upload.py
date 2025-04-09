from typing import TypedDict, Literal, Any, NewType

from datocms.types.locale import Localized
from .relationships import CreatorRelationships


__all__ = [
    "Color",
    "FocalPoint",
    "Metadata",
    "Attributes",
    "Upload",
    "UploadId",
    "UploadTypeName",
    "UploadTagId",
    "UploadTag",
    "UploadPermission",
    "UploadPermissionAttributes",
    "ManualUploadTag",
    "SmartUploadTag",
    "Attributes"
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


class Attributes(TypedDict):
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


UploadTypeName = Literal["upload"]


class Upload(TypedDict):
    id: UploadId
    type: UploadTypeName
    attributes: Attributes
    relationships: CreatorRelationships


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