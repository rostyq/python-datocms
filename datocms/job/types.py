from typing import Literal, TypedDict, NewType

from ..model.types import Model


__all__ = ["Payload", "Attributes", "JobResult", "JobResultId"]


JobResultId = NewType("JobResultId", str)


class Payload(TypedDict):
    data: Model


class Attributes(TypedDict):
    status: int
    payload: Payload | None


class JobResult(TypedDict):
    type: Literal["job_result"]
    id: JobResultId
    attributes: Attributes