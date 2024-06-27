from typing import cast, TYPE_CHECKING
from .api import ClientAPI
from ..model.types import Model
from ..job.types import JobResult


__all__ = ["ClientJob"]


class ClientJob(ClientAPI):
    job_results_endpoint = ClientAPI.urljoin("job-results/{id}")

    def get_job_result(self, id: str) -> tuple[int, Model]:
        response = self.session.get(
            self.job_results_endpoint.format(id=id), headers=self._api_headers()
        )
        data = cast(JobResult, self._handle_data_response(response))["attributes"]
        return data["status"], data["payload"]["data"]
