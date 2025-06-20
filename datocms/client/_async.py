from typing import (
    TYPE_CHECKING,
    AsyncGenerator,
    Any,
    Optional,
    cast,
)
from types import TracebackType
from asyncio import sleep

from httpx import (
    AsyncClient as _AsyncClient,
    USE_CLIENT_DEFAULT,
)

from .base import BaseClient, DatoApiError, DEFAULT_MAX_RETRIES, DEFAULT_RETRY_DELAY

if TYPE_CHECKING:
    from ..types.record import Record
    from ..types.model import Model
    from ..types.job import JobResult
    from ..types.upload import Upload, UploadPermission, UploadTag, UploadCollection
    from ..types.job import Job
    from .base import GetPageAsync


__all__ = ["AsyncClient"]


class AsyncClient(BaseClient):
    _client: _AsyncClient

    def __init__(self, token: str | None = None):
        super().__init__(token)
        self._client = _AsyncClient(
            auth=self._auth, base_url=self.base_url, follow_redirects=False
        )

    async def __aenter__(self):
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: Exception | None = None,
        traceback: TracebackType | None = None,
    ):
        await self._client.__aexit__(exc_type, exc_value, traceback)

    @staticmethod
    async def _iter_paginated[T](
        func: "GetPageAsync[T]", size: int | None = None, /
    ) -> AsyncGenerator[T, None]:
        offset: int = 0
        total: int = 1
        while offset < total:
            items, total = await func(limit=size, offset=offset)
            offset += len(items)

            for item in items:
                yield item

    async def execute(self, query, variables, **kwargs) -> "dict[str, Any] | None":
        response = await self._client.request(
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

    async def execute_from_file(
        self, path, variables, **kwargs
    ) -> dict[str, Any] | None:
        with open(path, "r") as fp:
            return await self.execute(fp.read(), variables, **kwargs)

    async def list_fields(self, id, *, timeout=None) -> list:
        response = await self._client.request(
            "GET",
            f"item-types/{id}/fields",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    async def get_job_result(
        self, id, *, timeout=None
    ) -> tuple[int, Optional["Model"]]:
        response = await self._client.request(
            "GET",
            f"job-results/{id}",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        data = cast("JobResult", self._handle_data_response(response))["attributes"]
        status, payload = data["status"], data.get("payload")
        return status, payload["data"] if payload else None

    async def poll_job(self, id, **kwargs) -> "Model":
        max_retries = kwargs.get("max_retries", DEFAULT_MAX_RETRIES)
        retry_delay = kwargs.get("retry_delay", DEFAULT_RETRY_DELAY)
        timeout = kwargs.get("timeout")

        for _ in range(max_retries):
            try:
                status, result = await self.get_job_result(id, timeout=timeout)
                if result is not None and status >= 200 and status < 300:
                    return result
            except DatoApiError as err:
                if err.code != "NOT_FOUND":
                    raise err
            await sleep(retry_delay)
        raise RuntimeError("Max retries exceeded")

    async def list_models(self, *, timeout=None) -> list["Model"]:
        response = await self._client.request(
            "GET",
            "item-types",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    async def list_records(self, **kwargs) -> "tuple[list[Record], int]":
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

        response = await self._client.request(
            "GET",
            "items",
            params=params,
            headers=self._api_headers,
            timeout=kwargs.get("timeout") or USE_CLIENT_DEFAULT,
        )
        return self._handle_list_response(response)

    def iter_records(self, page_size=None, **kwargs) -> AsyncGenerator["Record", None]:
        return self._iter_paginated(
            lambda offset, limit: self.list_records(
                **kwargs, offset=offset, limit=limit
            ),
            page_size,
        )

    async def request_upload_permission(
        self, filename, timeout=None
    ) -> "UploadPermission":
        response = await self._client.post(
            "upload-requests",
            headers=self._upload_headers,
            json=self._api_params("upload_request", filename=filename.lower()),
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        result: "UploadPermission" = self._handle_data_response(response)
        assert result.get("type") == "upload_request"
        return result

    async def create_upload_job(self, path, **kwargs) -> "Job":
        attributes = self._upload_params(
            path=path,
            copyright=kwargs.get("copyright"),
            author=kwargs.get("author"),
            notes=kwargs.get("notes"),
            metadata=kwargs.get("metadata"),
            tags=kwargs.get("tags"),
        )
        relationships = self._upload_relationships(
            collection_id=kwargs.get("collection_id"),
        )

        payload = self._api_params("upload", **attributes)
        if relationships:
            payload["data"]["relationships"] = relationships

        response = await self._client.post(
            "uploads",
            json=payload,
            headers=self._upload_headers,
            timeout=kwargs.get("timeout") or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    async def create_upload(self, filename, content, **kwargs):
        result = await self.request_upload_permission(
            filename, timeout=kwargs.get("timeout")
        )
        url = result["attributes"]["url"]
        headers = result["attributes"]["request_headers"]
        content_type = kwargs.get("content_type")
        if content_type is not None:
            headers["Content-Type"] = content_type

        response = await self._client.request(
            "PUT", url, headers=headers, content=content, auth=None
        )
        response.raise_for_status()
        job = await self.create_upload_job(
            result["id"],
            **{  # type: ignore[misc]
                k: v
                for k, v in kwargs.items()
                if k
                in (
                    "copyright",
                    "author",
                    "notes",
                    "metadata",
                    "tags",
                    "collection_id",
                    "timeout",
                )
            },
        )
        await sleep(retry_delay := kwargs.get("retry_delay", DEFAULT_RETRY_DELAY))
        return await self.poll_job(
            job["id"],
            max_retries=kwargs.get("max_retries", DEFAULT_MAX_RETRIES),
            retry_delay=retry_delay,
        )

    async def get_upload(self, id, timeout=None) -> "Upload":
        response = await self._client.request(
            "GET",
            f"uploads/{id}",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    async def update_upload(self, id, **kwargs) -> "Job":
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

        relationships = self._upload_relationships(
            collection_id=kwargs.get("collection_id"),
            creator=kwargs.get("creator"),
        )
        if relationships:
            params["relationships"] = relationships

        response = await self._client.request(
            "PUT",
            f"uploads/{id}",
            headers=self._upload_headers,
            json=self._api_update(id, "upload", **params),
            timeout=kwargs.get("timeout") or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    async def delete_upload(self, id, timeout=None) -> "Upload":
        response = await self._client.request(
            "DELETE",
            f"uploads/{id}",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    async def list_uploads(self, **kwargs) -> "tuple[list[Upload], int]":
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

        response = await self._client.request(
            "GET", "uploads", params=params, headers=self._api_headers
        )
        return self._handle_list_response(response)

    def iter_uploads(self, page_size=None, **kwargs) -> "AsyncGenerator[Upload, None]":
        return self._iter_paginated(
            lambda offset, limit: self.list_uploads(
                **kwargs, limit=limit, offset=offset
            ),
            page_size,
        )

    async def get_referenced_records_by_upload(self, id, **kwargs) -> list["Record"]:
        response = await self._client.request(
            "GET",
            f"uploads/{id}/references",
            headers=self._api_headers,
            params=self._records_params(
                nested=kwargs.get("nested", False), version=kwargs.get("version")
            ),
        )
        return self._handle_data_response(response)

    async def create_tag(self, **kwargs) -> str:
        response = await self._client.request(
            "POST",
            "upload-tags",
            headers=self._upload_headers,
            json=self._api_params("upload_tag", name=kwargs["name"]),
        )
        return self._handle_data_response(response)

    async def list_tags(self, **kwargs) -> "tuple[list[UploadTag], int]":
        self._page_params(
            params := {}, offset=kwargs.get("offset"), limit=kwargs.get("limit")
        )
        self._filter_params(params, query=kwargs.get("query"))
        response = await self._client.request(
            "GET",
            self._tags_endpoint(kwargs.get("tag", "manual")),
            headers=self._api_headers,
            params=params,
        )
        return self._handle_list_response(response)

    def iter_tags(self, page_size, **kwargs) -> "AsyncGenerator[UploadTag, None]":
        return self._iter_paginated(
            lambda offset, limit: self.list_tags(**kwargs, offset=offset, limit=limit),
            page_size,
        )

    async def list_upload_collections(self, **kwargs) -> "list[UploadCollection]":
        params = {}
        self._page_params(
            params, limit=kwargs.get("limit"), offset=kwargs.get("offset")
        )
        self._filter_params(
            params,
            ids=kwargs.get("ids"),
        )

        response = await self._client.request(
            "GET",
            "upload-collections",
            params=params,
            headers=self._api_headers,
            timeout=kwargs.get("timeout") or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)
