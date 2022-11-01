from typing import TypedDict, Literal, Any

from datocms.types.locale import Localized
from .relationships import CreatorRelationships


__all__ = [
    "Color",
    "FocalPoint",
    "Metadata",
    "Attributes",
    "Upload",
]


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


class Upload(TypedDict):
    id: str
    type: Literal["upload"]
    attributes: Attributes
    relationships: CreatorRelationships
