from typing import (
    TYPE_CHECKING,
    Iterable,
    Generator,
    Any,
    Optional,
    Unpack,
    cast,
)
from types import TracebackType
from time import sleep

from httpx import Client as _Client, USE_CLIENT_DEFAULT

from .base import BaseClient, DatoApiError, DEFAULT_MAX_RETRIES, DEFAULT_RETRY_DELAY

if TYPE_CHECKING:
    from ..types.api import (
        IterRecordsParams,
        IterUploadsParams,
        CreateUploadJobParams,
        IterTagsParams,
        ListRecordsWithPaginationParams,
        ListUploadsWithPaginationParams,
        ListTagsWithPaginationParams,
        GetReferencedRecordsByUploadParams,
        UpdateUploadParams,
    )
    from ..types.record import Record
    from ..types.model import Model
    from ..types.job import JobResult
    from ..types.upload import Upload, UploadPermission, UploadTag
    from ..types.job import Job

    from .base import GetPage


__all__ = ["Client"]


class Client(BaseClient):
    _client: _Client

    def __init__(self, token: str | None = None):
        super().__init__(token)
        self._client = _Client(
            auth=self._auth, base_url=self.base_url, follow_redirects=False
        )

    def __enter__(self):
        self._client.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: Exception | None = None,
        traceback: TracebackType | None = None,
    ):
        self._client.__exit__(exc_type, exc_value, traceback)

    @staticmethod
    def _iter_paginated[T](
        func: "GetPage[T]", size: int | None = None, /
    ) -> Generator[T, None, None]:
        offset: int = 0
        total: int = 1

        while offset < total:
            items, total = func(offset, limit=size)
            offset += len(items)
            yield from items

    def execute(self, query, variables, **kwargs) -> "dict[str, Any] | None":
        response = self._client.request(
            "POST",
            self.graphql_url,
            headers=self._graphql_headers(
                environment=kwargs.get("environment"),
                include_drafts=kwargs.get("include_drafts", False),
                exclude_invalid=kwargs.get("exclude_invalid"),
            ),
            json=self._graphql_payload(query, variables),
            timeout=kwargs.get("timeout") or USE_CLIENT_DEFAULT,
        )
        return self._handle_graphql_response(response)

    def execute_from_file(self, path, variables, **kwargs) -> "dict[str, Any] | None":
        with open(path, "r") as fp:
            return self.execute(fp.read(), variables, **kwargs)

    def list_fields(self, id, *, timeout=None) -> list:
        response = self._client.request(
            "GET",
            f"item-types/{id}/fields",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    def get_job_result(self, id, *, timeout=None) -> tuple[int, Optional["Model"]]:
        response = self._client.request(
            "GET",
            f"job-results/{id}",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        data = cast("JobResult", self._handle_data_response(response))["attributes"]
        status, payload = data["status"], data.get("payload")
        return status, payload["data"] if payload else None

    def poll_job(self, id, **kwargs) -> "Model":
        retry_delay = kwargs.get("retry_delay", DEFAULT_RETRY_DELAY)
        timeout = kwargs.get("timeout")

        for _ in range(kwargs.get("max_retries", DEFAULT_MAX_RETRIES)):
            try:
                status, result = self.get_job_result(id, timeout=timeout)
                if result is not None and status >= 200 and status < 300:
                    return result
            except DatoApiError as err:
                if err.code != "NOT_FOUND":
                    raise err
            sleep(retry_delay)
        raise RuntimeError("Max retries exceeded")

    def list_models(self, *, timeout=None) -> list["Model"]:
        response = self._client.request(
            "GET",
            "item-types",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    def list_records(
        self,
        **kwargs: "Unpack[ListRecordsWithPaginationParams]",
    ) -> "tuple[list[Record], int]":
        params = self._records_params(
            nested=kwargs.get("nested", False),
            locale=kwargs.get("locale"),
            order_by=kwargs.get("order_by"),
            version=kwargs.get("version"),
        )
        self._page_params(
            params, limit=kwargs.get("limit"), offset=kwargs.get("offset")
        )
        self._filter_params(
            params,
            ids=kwargs.get("ids"),
            types=kwargs.get("types"),
            query=kwargs.get("query"),
            fields=kwargs.get("fields"),
            only_valid=kwargs.get("only_valid", False),
        )

        response = self._client.request(
            "GET",
            "items",
            params=params,
            headers=self._api_headers,
            timeout=kwargs.get("timeout") or USE_CLIENT_DEFAULT,
        )
        return self._handle_list_response(response)

    def iter_records(
        self,
        page_size: int | None = None,
        **kwargs: "Unpack[IterRecordsParams]",
    ) -> "Generator[Record, None, None]":
        return self._iter_paginated(
            lambda offset, limit: self.list_records(
                limit=limit,
                offset=offset,
                **kwargs,
            ),
            page_size,
        )

    def request_upload_permission(
        self,
        filename,
        timeout=None,
    ) -> "UploadPermission":
        response = self._client.post(
            "upload-requests",
            headers=self._upload_headers,
            json=self._api_params("upload_request", filename=filename.lower()),
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        result: "UploadPermission" = self._handle_data_response(response)
        assert result.get("type") == "upload_request"
        return result

    def create_upload_job(
        self,
        path: str,
        **kwargs: "Unpack[CreateUploadJobParams]",
    ) -> "Job":
        attributes = self._upload_params(
            path=path,
            copyright=kwargs.get("copyright"),
            author=kwargs.get("author"),
            notes=kwargs.get("notes"),
            metadata=kwargs.get("metadata"),
            tags=kwargs.get("tags"),
        )
        response = self._client.post(
            "uploads",
            json=self._api_params("upload", **attributes),
            headers=self._upload_headers,
            timeout=kwargs.get("timeout") or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    def create_upload(self, filename, content: "bytes | Iterable[bytes]", **kwargs):
        result = self.request_upload_permission(filename)
        url = result["attributes"]["url"]
        headers = result["attributes"]["request_headers"]
        content_type = kwargs.get("content_type")
        if content_type is not None:
            headers["Content-Type"] = content_type

        self._client.request(
            "PUT", url, headers=headers, content=content, auth=None
        ).raise_for_status()
        job = self.create_upload_job(
            result["id"],
            **{  # type: ignore[misc]
                k: v
                for k, v in kwargs.items()
                if k in ("copyright", "author", "notes", "metadata", "tags", "timeout")
            },
        )
        sleep(kwargs.get("retry_delay", DEFAULT_RETRY_DELAY))
        return self.poll_job(
            job["id"],
            max_retries=kwargs.get("max_retries", DEFAULT_MAX_RETRIES),
            retry_delay=kwargs.get("retry_delay", DEFAULT_RETRY_DELAY),
        )

    def get_upload(self, id, timeout=None) -> "Upload":
        response = self._client.request(
            "GET",
            f"uploads/{id}",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    def update_upload(
        self,
        id: str,
        **kwargs: "Unpack[UpdateUploadParams]",
    ) -> "Job":
        params = {}
        attributes = self._upload_params(
            path=kwargs.get("path"),
            basename=kwargs.get("basename"),
            copyright=kwargs.get("copyright"),
            author=kwargs.get("author"),
            notes=kwargs.get("notes"),
            tags=kwargs.get("tags"),
            metadata=kwargs.get("metadata"),
        )
        if attributes:
            params["attributes"] = attributes

        if (creator := kwargs.get("creator")) is not None:
            params["relationships"] = {"creator": {"data": creator}}

        response = self._client.request(
            "PUT",
            f"uploads/{id}",
            headers=self._upload_headers,
            json=self._api_update(id, "upload", **params),
            timeout=kwargs.get("timeout") or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    def delete_upload(self, id, timeout=None) -> "Upload":
        response = self._client.request(
            "DELETE",
            f"uploads/{id}",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    def list_uploads(
        self,
        **kwargs: "Unpack[ListUploadsWithPaginationParams]",
    ) -> "tuple[list[Upload], int]":
        params = self._items_params(
            locale=kwargs.get("locale"), order_by=kwargs.get("order_by")
        )
        self._page_params(
            params, limit=kwargs.get("limit"), offset=kwargs.get("offset")
        )
        self._filter_params(
            params,
            ids=kwargs.get("ids"),
            query=kwargs.get("query"),
            fields=kwargs.get("fields"),
        )

        response = self._client.request(
            "GET", "uploads", params=params, headers=self._api_headers
        )
        return self._handle_list_response(response)

    def iter_uploads(
        self,
        page_size: "int | None" = None,
        **kwargs: "Unpack[IterUploadsParams]",
    ) -> "Generator[Upload, None, None]":
        return self._iter_paginated(
            lambda offset, limit: self.list_uploads(
                order_by=kwargs.get("order_by"),
                locale=kwargs.get("locale"),
                ids=kwargs.get("ids"),
                query=kwargs.get("query"),
                fields=kwargs.get("fields"),
                limit=limit,
                offset=offset,
            ),
            page_size,
        )

    def get_referenced_records_by_upload(
        self,
        id: str,
        **kwargs: "Unpack[GetReferencedRecordsByUploadParams]",
    ) -> list["Record"]:
        response = self._client.request(
            "GET",
            f"uploads/{id}/references",
            headers=self._api_headers,
            params=self._records_params(
                nested=kwargs.get("nested", False), version=kwargs.get("version")
            ),
        )
        return self._handle_data_response(response)

    def create_tag(self, **kwargs) -> str:
        response = self._client.request(
            "POST",
            "upload-tags",
            headers=self._upload_headers,
            json=self._api_params("upload_tag", name=kwargs["name"]),
        )
        return self._handle_data_response(response)

    def list_tags(
        self,
        **kwargs: "Unpack[ListTagsWithPaginationParams]",
    ) -> "tuple[list[UploadTag], int]":
        self._page_params(
            params := {}, offset=kwargs.get("offset"), limit=kwargs.get("limit")
        )
        self._filter_params(params, query=kwargs.get("query"))
        response = self._client.request(
            "GET",
            self._tags_endpoint(kwargs.get("tag", "manual")),
            headers=self._api_headers,
            params=params,
        )
        return self._handle_list_response(response)

    def iter_tags(
        self,
        page_size: "int | None" = None,
        **kwargs: "Unpack[IterTagsParams]",
    ) -> "Generator[UploadTag, None, None]":
        return self._iter_paginated(
            lambda offset, limit: self.list_tags(
                tag=kwargs.get("tag", "manual"), limit=limit, offset=offset
            ),
            page_size,
        )
