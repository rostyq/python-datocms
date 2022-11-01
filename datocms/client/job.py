from typing import cast
from ..types import JobResult, ItemType
from .api import ClientAPI


__all__ = ["ClientJob"]


class ClientJob(ClientAPI):
    job_results_endpoint = ClientAPI.urljoin("job-results/{id}")

    def get_job_result(self, id: str) -> tuple[int, ItemType]:
        response = self.session.get(self.job_results_endpoint.format(id=id))
        data = cast(JobResult, self._handle_data_response(response))["attributes"]
        return data["status"], data["payload"]["data"]
