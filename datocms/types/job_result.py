from typing import Literal, TypedDict

from .item_type import ItemType


__all__ = ["Payload", "Attributes", "JobResult"]


class Payload(TypedDict):
    data: ItemType


class Attributes(TypedDict):
    status: int
    payload: Payload | None


class JobResult(TypedDict):
    type: Literal["job_result"]
    id: str
    attributes: Attributes