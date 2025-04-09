from typing import Literal, TypedDict, NewType, NotRequired

from .model import Model


__all__ = ["Payload", "Attributes", "JobResult", "JobResultId", "Job"]


JobResultId = NewType("JobResultId", str)


class Job(TypedDict):
    type: Literal["job"]
    id: str


class Payload(TypedDict):
    data: Model


class Attributes(TypedDict):
    status: int
    payload: NotRequired[Payload]


class JobResult(TypedDict):
    type: Literal["job_result"]
    id: JobResultId
    attributes: Attributes