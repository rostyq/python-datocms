from typing import TypedDict, Literal


__all__ = [
    "UploadTag",
    "ManualUploadTag",
    "SmartUploadTag",
    "Attributes"
]


class Attributes(TypedDict):
    name: str


class UploadTag(TypedDict):
    id: str
    type: Literal["upload_tag", "upload_smart_tag"]
    attributes: Attributes


class ManualUploadTag(UploadTag):
    type: Literal["upload_tag"]


class SmartUploadTag(UploadTag):
    type: Literal["upload_smart_tag"]
