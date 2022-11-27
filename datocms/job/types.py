from typing import Literal, TypedDict

from ..model.types import Model


__all__ = ["Payload", "Attributes", "JobResult"]


class Payload(TypedDict):
    data: Model


class Attributes(TypedDict):
    status: int
    payload: Payload | None


class JobResult(TypedDict):
    type: Literal["job_result"]
    id: str
    attributes: Attributes