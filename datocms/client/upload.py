from requests import put
from typing import IO, Generator, Literal

from .job import ClientJob

from ..job.job import Job
from ..upload.types import Metadata, Upload
from ..record.types import Record


__all__ = ["ClientUpload"]


class ClientUpload(ClientJob):
    uploads_endpoint = ClientJob.urljoin("uploads")
    upload_requests_endpoint = ClientJob.urljoin("upload-requests")

    upload_endpoint = "%s/{id}" % uploads_endpoint
    referenced_records_by_upload_endpoint = "%s/references" % upload_endpoint

    @staticmethod
    def _upload_headers() -> dict:
        return {"Content-Type": "application/vnd.api+json"}

    def create_upload(
        self,
        filename: str,
        content: str | bytes | IO,
        copyright: str | None = None,
        author: str | None = None,
        notes: str | None = None,
        default_field_metadata: dict[str, Metadata] | None = None,
        tags: list[str] | None = None,
    ) -> Job:
        response = self.session.post(
            self.upload_requests_endpoint,
            headers=self._api_headers() | self._upload_headers(),
            json=self._api_parameters("upload_request", filename=filename.lower()),
        )
        response.raise_for_status()
        result = response.json()["data"]

        path = result["id"]

        response = put(result["attributes"]["url"], data=content)
        response.raise_for_status()

        attributes = {"path": path}

        if copyright is not None:
            attributes["copyright"] = copyright
        if author is not None:
            attributes["author"] = author
        if notes is not None:
            attributes["notes"] = notes
        if default_field_metadata is not None:
            attributes["default_field_metadata"] = default_field_metadata
        if tags is not None:
            attributes["tags"] = tags

        response = self.session.post(
            self.uploads_endpoint,
            json=self._api_parameters("upload", **attributes),
            headers=self._api_headers() | self._upload_headers(),
        )
        data = self._handle_data_response(response)
        return Job(client=self, id=data["id"])

    def get_upload(self, id: str) -> Upload:
        response = self.session.get(
            f"{self.uploads_endpoint}/{id}", headers=self._api_headers()
        )
        return self._handle_data_response(response)

    def delete_upload(self, id: str) -> Upload:
        response = self.session.delete(
            f"{self.uploads_endpoint}/{id}", headers=self._api_headers()
        )
        return self._handle_data_response(response)

    def list_uploads(
        self,
        ids: str | None = None,
        query: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        locale: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> tuple[list[Upload], int]:
        params = self._page_params(offset, limit) | self._filter_params(
            ids=ids, query=query, fields=fields
        )

        if locale is not None:
            params["locale"] = locale
        if order_by is not None:
            params["order_by"] = order_by

        response = self.session.get(
            self.uploads_endpoint, params=params, headers=self._api_headers()
        )
        return self._handle_list_response(response)

    def iter_uploads(
        self,
        ids: str | None = None,
        query: str | None = None,
        fields: str | None = None,
        order_by: str | None = None,
        locale: str | None = None,
        page: int | None = None,
    ) -> Generator[Upload, None, None]:
        return self._iter_paginated(
            self.list_uploads,
            page=page,
            order_by=order_by,
            locale=locale,
            ids=ids,
            query=query,
            fields=fields,
        )

    def get_referenced_records_by_upload(
        self,
        id: str,
        nested: bool = False,
        version: Literal["current", "published", "published-or-current"] | None = None,
    ) -> list[Record]:
        params = {}

        if nested is True:
            params["nested"] = "true"
        if version is not None:
            params["version"] = version

        response = self.session.get(
            self.referenced_records_by_upload_endpoint.format(id=id),
            headers=self._api_headers(),
            params=params,
        )

        return response.json()["data"]
