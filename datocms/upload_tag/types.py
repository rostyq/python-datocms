from typing import TypedDict, Literal, NewType


__all__ = [
    "UploadTagId",
    "UploadTag",
    "ManualUploadTag",
    "SmartUploadTag",
    "Attributes"
]


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
