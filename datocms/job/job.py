from typing import Generic, TypeVar
from ..client.job import ClientJob


__all__ = ["Job"]


T = TypeVar("T", bound=ClientJob)


class Job(Generic[T]):
    id: str
    client: T

    def __init__(self, id: str, client: T):
        self.id = id
        self.client = client

    def __repr__(self) -> str:
        return f"Job(id={self.id})"

    def result(self):
        return self.client.get_job_result(self.id)