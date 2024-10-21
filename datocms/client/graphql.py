from os import PathLike
from requests import Request

from .base import ClientBase

from .types.params import PayloadGraphQL


__all__ = ["ClientGraphQL"]


class ClientGraphQL(ClientBase):
    graphql_endpoint = "https://graphql.datocms.com"

    @staticmethod
    def _graphql_headers() -> dict:
        return {"Content-Type": "application/json"}

    @staticmethod
    def _graphql_payload(query: str, **kwargs):
        payload = PayloadGraphQL(query=query)
        if len(kwargs) != 0:
            payload["variables"] = kwargs

        return payload

    @classmethod
    def _graphql_request(cls, query: str, **kwargs):
        return Request(
            "POST",
            cls.graphql_endpoint,
            headers=cls._graphql_headers(),
            json=cls._graphql_payload(query, **kwargs),
        )

    def execute(
        self,
        query: str,
        environment: str | None = None,
        include_drafts: bool = False,
        exclude_invalid: bool | None = None,
        **kwargs,
    ) -> dict[str]:
        request = self._graphql_request(query, **kwargs)
        request = self.session.prepare_request(request)

        if environment is not None:
            request.headers["X-Environment"] = environment
        if include_drafts:
            request.headers["X-Include-Drafts"] = True
        if exclude_invalid is not None:
            request.headers["X-Exclude-Invalid"] = exclude_invalid

        response = self.session.send(request)
        return self._handle_data_response(response)

    def execute_from_file(
        self,
        path: PathLike,
        environment: str | None = None,
        include_drafts: bool = False,
        exclude_invalid: bool | None = None,
        **kwargs,
    ) -> dict[str]:
        with open(path, "r") as fp:
            return self.execute(
                fp.read(),
                environment=environment,
                include_drafts=include_drafts,
                exclude_invalid=exclude_invalid,
                **kwargs,
            )
