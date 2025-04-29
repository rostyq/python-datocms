from typing import (
    TYPE_CHECKING,
    Literal,
    Iterable,
    AsyncIterable,
    Protocol,
    Generic,
    TypeVar,
    Generator,
    AsyncGenerator,
    cast,
    Any,
    Optional,
    MutableMapping,
    Mapping,
)
from types import TracebackType
from os import environ, PathLike
from time import sleep as sync_sleep
from asyncio import sleep as async_sleep

from httpx import (
    Auth,
    Request,
    Response,
    Client as _Client,
    AsyncClient as _AsyncClient,
    USE_CLIENT_DEFAULT,
)

if TYPE_CHECKING:
    from httpx._types import TimeoutTypes

    from .types.api import *
    from .types.errors import ErrorAttributes, Error, ErrorCodeType
    from .types.record import Record
    from .types.model import Model
    from .types.job import JobResult
    from .types.upload import Metadata, Upload, Localized, UploadPermission, UploadTag
    from .types.job import Job
    from .types.relationships import CreatorId


__all__ = ["Client", "AsyncClient"]


T = TypeVar("T")

DEFAULT_RETRY_DELAY = 1.0
DEFAULT_MAX_RETRIES = 10


class GetPage(Protocol, Generic[T]):
    def __call__(self, limit: int, offset: int, **kwargs) -> tuple[list[T], int]: ...


class GetPageAsync(Protocol, Generic[T]):
    async def __call__(
        self, limit: int, offset: int, **kwargs
    ) -> tuple[list[T], int]: ...


class DatoAuth(Auth):
    def __init__(self, token: str):
        self._token = token

    def auth_flow(self, request: Request):
        request.headers["Authorization"] = f"Bearer {self._token}"
        yield request


class DatoError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

    @classmethod
    def from_dict(cls, data: dict[str, Any], /):
        raise NotImplementedError(
            f"{cls.__name__}.from_dict() must be implemented in subclasses"
        )


class DatoGraphqlError(DatoError):
    def __init__(
        self,
        message: str,
        locations: list["ErrorLocation"],
        path: list[str] | None = None,
        extensions: "Optional[ErrorExtensions]" = None,
    ):
        super().__init__()
        self.message = message
        self.locations = locations
        self.path = path
        self.extensions = extensions

    @classmethod
    def from_dict(cls, data: "GraphqlError", /):
        print(data)
        return cls(
            message=data["message"],
            locations=data["locations"],
            path=data.get("path"),
            extensions=data.get("extensions"),
        )

    def _fmt_locs(self) -> str:
        if len(self.locations) == 1:
            loc = self.locations[0]
            return f"line {loc['line']}, column {loc['column']}"
        else:
            return ", ".join(f"{loc['line']}:{loc['column']}" for loc in self.locations)


    def _fmt_path(self) -> str:
        return ".".join(self.path) if self.path else ""

    def _fmt_err(self) -> str:
        return f"{self.message} at ({self._fmt_locs()})"

    def __str__(self):
        message_array = [self.message, "at", self._fmt_locs()]
        if self.path:
            message_array.extend(["in", self._fmt_path()])
        return " ".join(message_array)


class DatoApiError(DatoError):
    code: "ErrorCodeType"

    def __init__(
        self, code: str, doc_url: str, details: dict[str, Any], transient: bool
    ):
        super().__init__()
        self.code = code
        self.doc_url = doc_url
        self.details = details
        self.transient = transient

    @classmethod
    def from_dict(cls, data: "ErrorAttributes", /):
        return cls(
            code=data["code"],
            doc_url=data["doc_url"],
            details=data["details"],
            transient=data.get("transient", False),
        )

    def __str__(self) -> str:
        return f"{self.code}{': %s' % self.details if self.details else ''}. See {self.doc_url} for more details."


class BaseClient:
    base_url: str = "https://site-api.datocms.com"
    graphql_url: str = "https://graphql.datocms.com"

    _api_headers = {"X-Api-Version": "3", "Accept": "application/json"}
    _upload_headers = {**_api_headers, "Content-Type": "application/vnd.api+json"}

    _auth: DatoAuth

    def __init__(self, token: str | None = None):
        self._auth = DatoAuth(token or environ["DATOCMS_API_TOKEN"])

    @staticmethod
    def _handle_response(response: "Response") -> dict[str, Any]:
        result = (
            response.json()
            if "application/json" in response.headers["Content-Type"]
            else None
        )

        if response.is_success:
            return result
        elif result is not None and isinstance(data := result["data"], list):
            data: list["Error"]
            errors = [DatoApiError.from_dict(item["attributes"]) for item in data]
            if len(errors) == 1:
                raise errors[0]
            else:
                raise ExceptionGroup(",".join(error.code for error in errors), errors)
        else:
            response.raise_for_status()

    @staticmethod
    def _handle_graphql_response(response: "Response") -> dict[str, Any] | None:
        result: "GraphqlResult" = response.raise_for_status().json()
        if (errors := result.get("errors")) is None:
            return result.get("data")
        else:
            errors = [DatoGraphqlError.from_dict(error) for error in errors]
            if len(errors) == 1:
                raise errors[0]
            else:
                raise ExceptionGroup("GraphQL errors", errors)

    @classmethod
    def _handle_data_response(cls, response: "Response") -> dict[str, Any]:
        return cls._handle_response(response)["data"]

    @classmethod
    def _handle_list_response(cls, response: "Response") -> tuple[list[T], int]:
        return cls._list_result_to_tuple(cls._handle_response(response))

    @staticmethod
    def _page_params(
        p: MutableMapping[str, Any],
        limit: int | None = None,
        offset: int | None = None,
    ):
        if limit is not None:
            if limit > 0 and limit <= 500:
                p["page[limit]"] = limit
            else:
                raise ValueError("Limit must be between 1 and 500")
        if offset is not None:
            if offset >= 0:
                p["page[offset]"] = offset
            else:
                raise ValueError("Offset must be greater than or equal to 0")

    @staticmethod
    def _filter_params(
        p: MutableMapping[str, Any],
        ids: Optional[Iterable[str]] = None,
        types: Optional[Iterable[str]] = None,
        query: str | None = None,
        fields: Mapping[str, Mapping[str, str]] | None = None,
        only_valid: bool = False,
    ):
        if ids is not None:
            if types is None and fields is None:
                p["filter[ids]"] = ",".join(ids)
            else:
                raise ValueError("Cannot use both ids and type/fields filters")
        if types is not None:
            if ids is None:
                ftype = p["filter[type]"] = ",".join(types)
                if ftype.count(",") > 1 and fields is not None:
                    raise ValueError(
                        "Cannot use both multiple types and fields filters"
                    )
            else:
                raise ValueError("Cannot use both ids and type filters")
        if query is not None:
            if ids is None:
                p["filter[query]"] = query
            else:
                raise ValueError("Cannot use both ids and query filters")
        if fields is not None:
            for field, conditions in fields.items():
                if not isinstance(conditions, dict):
                    raise ValueError(
                        "Each field must map to a dictionary of conditions"
                    )
                for condition, value in conditions.items():
                    p[f"filter[fields][{field}][{condition}]"] = str(value)
        if only_valid:
            p["filter[only_valid]"] = "true"

    @staticmethod
    def _items_params(locale: str | None = None, order_by: str | None = None):
        p = {}
        if locale is not None:
            p["locale"] = locale
        if order_by is not None:
            p["order_by"] = order_by
        return p

    @staticmethod
    def _tags_endpoint(tag: "TagType", /) -> str:
        match tag:
            case "manual":
                return "upload-tags"
            case "smart":
                return "upload-smart-tags"
            case _:
                raise ValueError(f"Unknown tag type: {tag}")

    @classmethod
    def _records_params(
        cls,
        nested: bool = False,
        locale: str | None = None,
        order_by: str | None = None,
        version: "Optional[Version]" = None,
    ):
        p = cls._items_params(locale=locale, order_by=order_by)
        if nested:
            p["nested"] = "true"
        if version is not None:
            p["version"] = version
        return p

    @staticmethod
    def _upload_params(
        path: str | None = None,
        basename: str | None = None,
        copyright: str | None = None,
        author: str | None = None,
        notes: str | None = None,
        metadata: "Optional[Localized[Metadata]]" = None,
        tags: list[str] | None = None,
    ):
        p = {}
        if path is not None:
            p["path"] = path
        if basename is not None:
            p["basename"] = basename
        if copyright is not None:
            p["copyright"] = copyright
        if author is not None:
            p["author"] = author
        if notes is not None:
            p["notes"] = notes
        if metadata is not None:
            p["default_field_metadata"] = metadata
        if tags is not None:
            p["tags"] = tags
        return p

    @staticmethod
    def _api_params(name: str, /, **attributes) -> "Payload":
        return {"data": {"type": name, "attributes": attributes}}

    @staticmethod
    def _api_update(id: str, name: str, **kwargs) -> "Payload":
        return {"data": {"id": id, "type": name, **kwargs}}

    @staticmethod
    def _list_result_to_tuple(result: "ArrayResult") -> tuple[list[T], int]:
        return result["data"], result["meta"]["total_count"]

    @staticmethod
    def _graphql_payload(
        query: str, variables: Mapping[str, Any] | None = None
    ) -> "PayloadGraphQL":
        payload: "PayloadGraphQL" = {"query": query}
        if variables is not None and len(variables) != 0:
            payload["variables"] = variables
        return payload

    @staticmethod
    def _graphql_headers(
        environment: str | None = None,
        include_drafts: bool = False,
        exclude_invalid: bool | None = None,
    ) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if environment is not None:
            headers["X-Environment"] = environment
        if include_drafts:
            headers["X-Include-Drafts"] = "true"
        if exclude_invalid is not None:
            headers["X-Exclude-Invalid"] = "true" if exclude_invalid else "false"
        return headers


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
    def _iter_paginated(
        func: GetPage[T], page_size: int = 30, /, **kwargs
    ) -> Generator[T, None, None]:
        offset: int = 0
        total: int = 1

        while offset < total:
            items, total = func(limit=page_size, offset=offset, **kwargs)
            offset += len(items)

            for item in items:
                yield item

    def execute(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
        *,
        environment: str | None = None,
        include_drafts: bool = False,
        exclude_invalid: bool | None = None,
        timeout: "Optional[TimeoutTypes]" = None,
    ) -> dict[str, Any]:
        response = self._client.request(
            "POST",
            self.graphql_url,
            headers=self._graphql_headers(
                environment=environment,
                include_drafts=include_drafts,
                exclude_invalid=exclude_invalid,
            ),
            json=self._graphql_payload(query, variables),
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_graphql_response(response)

    def execute_from_file(
        self,
        path: PathLike,
        variables: dict[str, Any] | None = None,
        *,
        environment: str | None = None,
        include_drafts: bool = False,
        exclude_invalid: bool | None = None,
        timeout: "Optional[TimeoutTypes]" = None,
    ) -> dict[str, Any]:
        with open(path, "r") as fp:
            return self.execute(
                fp.read(),
                variables,
                environment=environment,
                include_drafts=include_drafts,
                exclude_invalid=exclude_invalid,
                timeout=timeout,
            )

    def list_fields(self, id: str, *, timeout: "Optional[TimeoutTypes]" = None) -> list:
        response = self._client.request(
            "GET",
            f"item-types/{id}/fields",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    def get_job_result(
        self, id: str, *, timeout: "Optional[TimeoutTypes]" = None
    ) -> tuple[int, "Model"]:
        response = self._client.request(
            "GET",
            f"job-results/{id}",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        data = cast("JobResult", self._handle_data_response(response))["attributes"]
        status, payload = data["status"], data["payload"]
        return status, payload["data"] if payload else None

    def poll_job(
        self,
        id: str,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        timeout: "Optional[TimeoutTypes]" = None,
    ):
        for _ in range(max_retries):
            try:
                status, result = self.get_job_result(id, timeout=timeout)
                if result is not None and status >= 200 and status < 300:
                    return result
            except DatoApiError as err:
                if err.code != "NOT_FOUND":
                    raise err
            sync_sleep(retry_delay)
        raise RuntimeError("Max retries exceeded")

    def list_models(self, *, timeout: "Optional[TimeoutTypes]" = None) -> list["Model"]:
        response = self._client.request(
            "GET",
            "item-types",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    def list_records(
        self,
        *,
        nested: bool = False,
        ids: Iterable[str] | None = None,
        types: Iterable[str] | None = None,
        query: str | None = None,
        fields: Mapping[str, Mapping[str, str]] | None = None,
        only_valid: bool = False,
        locale: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        version: "Optional[Version]" = None,
        timeout: "Optional[TimeoutTypes]" = None,
    ) -> tuple[list["Record"], int]:
        params = self._records_params(
            nested=nested,
            locale=locale,
            order_by=order_by,
            version=version,
        )
        self._page_params(params, limit=limit, offset=offset)
        self._filter_params(
            params,
            ids=ids,
            types=types,
            query=query,
            fields=fields,
            only_valid=only_valid,
        )

        response = self._client.request(
            "GET",
            "items",
            params=params,
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_list_response(response)

    def iter_records(
        self,
        page_size: int = 30,
        *,
        nested: bool = False,
        ids: Iterable[str] | None = None,
        types: Iterable[str] | None = None,
        query: str | None = None,
        fields: Mapping[str, Mapping[str, str]] | None = None,
        only_valid: bool = False,
        locale: str | None = None,
        order_by: str | None = None,
        version: "Optional[Version]" = None,
        timeout: "Optional[TimeoutTypes]" = None,
    ) -> Generator["Record", None, None]:
        return self._iter_paginated(
            self.list_records,
            page_size,
            nested=nested,
            ids=ids,
            types=types,
            query=query,
            fields=fields,
            only_valid=only_valid,
            locale=locale,
            order_by=order_by,
            version=version,
            timeout=timeout,
        )

    def request_upload_permission(
        self,
        filename: str,
        timeout: "Optional[TimeoutTypes]" = None,
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
        copyright: str | None = None,
        author: str | None = None,
        notes: str | None = None,
        metadata: "Optional[Localized[Metadata]]" = None,
        tags: list[str] | None = None,
        timeout: "Optional[TimeoutTypes]" = None,
    ) -> "Job":
        attributes = self._upload_params(
            path=path,
            copyright=copyright,
            author=author,
            notes=notes,
            metadata=metadata,
            tags=tags,
        )
        response = self._client.post(
            "uploads",
            json=self._api_params("upload", **attributes),
            headers=self._upload_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    def create_upload(
        self,
        filename: str,
        content: bytes | Iterable[bytes],
        content_type: str | None = None,
        copyright: str | None = None,
        author: str | None = None,
        notes: str | None = None,
        metadata: "Optional[Localized[Metadata]]" = None,
        tags: list[str] | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        result = self.request_upload_permission(filename)
        url = result["attributes"]["url"]
        headers = result["attributes"]["request_headers"]
        if content_type is not None:
            headers["Content-Type"] = content_type

        response = self._client.request(
            "PUT", url, headers=headers, content=content, auth=None
        )
        response.raise_for_status()
        job = self.create_upload_job(
            result["id"],
            copyright=copyright,
            author=author,
            notes=notes,
            metadata=metadata,
            tags=tags,
        )
        sync_sleep(retry_delay)
        return self.poll_job(
            job["id"], max_retries=max_retries, retry_delay=retry_delay
        )

    def get_upload(self, id: str, timeout: "Optional[TimeoutTypes]" = None) -> "Upload":
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
        path: str | None = None,
        basename: str | None = None,
        copyright: str | None = None,
        author: str | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
        metadata: "Optional[Localized[Metadata]]" = None,
        creator: "Optional[CreatorId]" = None,
        timeout: "Optional[TimeoutTypes]" = None,
    ) -> "Job":
        params = {}
        attributes = self._upload_params(
            path=path,
            basename=basename,
            copyright=copyright,
            author=author,
            notes=notes,
            tags=tags,
            metadata=metadata,
        )
        if attributes:
            params["attributes"] = attributes

        if creator is not None:
            params["relationships"] = {"creator": {"data": creator}}

        response = self._client.request(
            "PUT",
            f"uploads/{id}",
            headers=self._upload_headers(),
            json=self._api_update(id, "upload", **params),
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    def delete_upload(
        self, id: str, timeout: "Optional[TimeoutTypes]" = None
    ) -> "Upload":
        response = self._client.request(
            "DELETE",
            f"uploads/{id}",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    def list_uploads(
        self,
        ids: Iterable[str] | None = None,
        query: str | None = None,
        fields: Mapping[str, Mapping[str, str]] | None = None,
        order_by: str | None = None,
        locale: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> tuple[list["Upload"], int]:
        params = self._items_params(locale=locale, order_by=order_by)
        self._page_params(params, limit=limit, offset=offset)
        self._filter_params(
            params,
            ids=ids,
            query=query,
            fields=fields,
        )

        response = self._client.request(
            "GET", "uploads", params=params, headers=self._api_headers
        )
        return self._handle_list_response(response)

    def iter_uploads(
        self,
        page_size: int = 30,
        *,
        ids: Iterable[str] | None = None,
        query: str | None = None,
        fields: Mapping[str, Mapping[str, str]] | None = None,
        order_by: str | None = None,
        locale: str | None = None,
    ) -> Generator["Upload", None, None]:
        return self._iter_paginated(
            self.list_uploads,
            page=page_size,
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
        version: "Optional[AnyVersion]" = None,
    ) -> list["Record"]:
        response = self._client.request(
            "GET",
            f"uploads/{id}/references",
            headers=self._api_headers,
            params=self._records_params(nested=nested, version=version),
        )
        return self._handle_data_response(response)

    def create_tag(self, name: str) -> str:
        response = self._client.request(
            "POST",
            "upload-tags",
            headers=self._upload_headers,
            json=self._api_params("upload_tag", name=name),
        )
        return self._handle_data_response(response)

    def list_tags(
        self,
        tag: "TagType" = "manual",
        query: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> tuple[list["UploadTag"], int]:
        self._page_params(params := {}, offset=offset, limit=limit)
        self._filter_params(params, query=query)
        response = self._client.request(
            "GET",
            self._tags_endpoint(tag),
            headers=self._api_headers,
            params=params,
        )
        return self._handle_list_response(response)

    def iter_tags(
        self,
        page_size: int = 30,
        *,
        tag: "TagType" = "manual",
    ) -> Generator["UploadTag", None, None]:
        return self._iter_paginated(self.list_tags, page_size, tag=tag)


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
    async def _iter_paginated(
        func: GetPageAsync[T], page_size: int = 30, /, **kwargs
    ) -> AsyncGenerator[T, None]:
        offset: int = 0
        total: int = 1

        while offset < total:
            items, total = await func(limit=page_size, offset=offset, **kwargs)
            offset += len(items)

            for item in items:
                yield item

    async def execute(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
        *,
        environment: str | None = None,
        include_drafts: bool = False,
        exclude_invalid: bool | None = None,
        timeout: "Optional[TimeoutTypes]" = None,
    ) -> dict[str, Any] | None:
        response = await self._client.request(
            "POST",
            self.graphql_url,
            headers=self._graphql_headers(
                environment=environment,
                include_drafts=include_drafts,
                exclude_invalid=exclude_invalid,
            ),
            json=self._graphql_payload(query, variables),
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_graphql_response(response)

    async def execute_from_file(
        self,
        path: PathLike,
        variables: dict[str, Any] | None = None,
        *,
        environment: str | None = None,
        include_drafts: bool = False,
        exclude_invalid: bool | None = None,
        timeout: "Optional[TimeoutTypes]" = None,
    ) -> dict[str, Any] | None:
        with open(path, "r") as fp:
            return await self.execute(
                fp.read(),
                variables,
                environment=environment,
                include_drafts=include_drafts,
                exclude_invalid=exclude_invalid,
                timeout=timeout,
            )

    async def list_fields(
        self, id: str, *, timeout: "Optional[TimeoutTypes]" = None
    ) -> list:
        response = await self._client.request(
            "GET",
            f"item-types/{id}/fields",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    async def get_job_result(
        self, id: str, *, timeout: "Optional[TimeoutTypes]" = None
    ) -> tuple[int, "Model"]:
        response = await self._client.request(
            "GET",
            f"job-results/{id}",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        data = cast("JobResult", self._handle_data_response(response))["attributes"]
        status, payload = data["status"], data["payload"]
        return status, payload["data"] if payload else None

    async def poll_job(
        self,
        id: str,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        timeout: "Optional[TimeoutTypes]" = None,
    ):
        for _ in range(max_retries):
            try:
                status, result = await self.get_job_result(id, timeout=timeout)
                if result is not None and status >= 200 and status < 300:
                    return result
            except DatoApiError as err:
                if err.code != "NOT_FOUND":
                    raise err
            await async_sleep(retry_delay)
        raise RuntimeError("Max retries exceeded")

    async def list_models(
        self, *, timeout: "Optional[TimeoutTypes]" = None
    ) -> list["Model"]:
        response = await self._client.request(
            "GET",
            "item-types",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    async def list_records(
        self,
        *,
        nested: bool = False,
        ids: Iterable[str] | None = None,
        types: Iterable[str] | None = None,
        query: str | None = None,
        fields: Mapping[str, Mapping[str, str]] | None = None,
        only_valid: bool = False,
        locale: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        version: "Optional[Version]" = None,
        timeout: "Optional[TimeoutTypes]" = None,
    ) -> tuple[list["Record"], int]:
        params = self._records_params(
            nested=nested,
            locale=locale,
            order_by=order_by,
            version=version,
        )
        self._page_params(params, limit=limit, offset=offset)
        self._filter_params(
            params,
            ids=ids,
            types=types,
            query=query,
            fields=fields,
            only_valid=only_valid,
        )

        response = await self._client.request(
            "GET",
            "items",
            params=params,
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_list_response(response)

    def iter_records(
        self,
        page_size: int = 30,
        *,
        nested: bool = False,
        ids: Iterable[str] | None = None,
        types: Iterable[str] | None = None,
        query: str | None = None,
        fields: Mapping[str, Mapping[str, str]] | None = None,
        only_valid: bool = False,
        locale: str | None = None,
        order_by: str | None = None,
        version: "Optional[Version]" = None,
        timeout: "Optional[TimeoutTypes]" = None,
    ) -> AsyncGenerator["Record", None]:
        return self._iter_paginated(
            self.list_records,
            page_size,
            nested=nested,
            ids=ids,
            types=types,
            query=query,
            fields=fields,
            only_valid=only_valid,
            locale=locale,
            order_by=order_by,
            version=version,
            timeout=timeout,
        )

    async def request_upload_permission(
        self,
        filename: str,
        timeout: "Optional[TimeoutTypes]" = None,
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

    async def create_upload_job(
        self,
        path: str,
        copyright: str | None = None,
        author: str | None = None,
        notes: str | None = None,
        metadata: "Optional[Localized[Metadata]]" = None,
        tags: list[str] | None = None,
        timeout: "Optional[TimeoutTypes]" = None,
    ) -> "Job":
        attributes = self._upload_params(
            path=path,
            copyright=copyright,
            author=author,
            notes=notes,
            metadata=metadata,
            tags=tags,
        )
        response = await self._client.post(
            "uploads",
            json=self._api_params("upload", **attributes),
            headers=self._upload_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    async def create_upload(
        self,
        filename: str,
        content: bytes | Iterable[bytes] | AsyncIterable[bytes],
        content_type: str | None = None,
        copyright: str | None = None,
        author: str | None = None,
        notes: str | None = None,
        metadata: "Optional[Localized[Metadata]]" = None,
        tags: list[str] | None = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        result = await self.request_upload_permission(filename)
        url = result["attributes"]["url"]
        headers = result["attributes"]["request_headers"]
        if content_type is not None:
            headers["Content-Type"] = content_type

        response = await self._client.request(
            "PUT", url, headers=headers, content=content, auth=None
        )
        response.raise_for_status()
        job = await self.create_upload_job(
            result["id"],
            copyright=copyright,
            author=author,
            notes=notes,
            metadata=metadata,
            tags=tags,
        )
        await async_sleep(retry_delay)
        return await self.poll_job(
            job["id"], max_retries=max_retries, retry_delay=retry_delay
        )

    async def get_upload(
        self, id: str, timeout: "Optional[TimeoutTypes]" = None
    ) -> "Upload":
        response = await self._client.request(
            "GET",
            f"uploads/{id}",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    async def delete_upload(
        self, id: str, timeout: "Optional[TimeoutTypes]" = None
    ) -> "Upload":
        response = await self._client.request(
            "DELETE",
            f"uploads/{id}",
            headers=self._api_headers,
            timeout=timeout or USE_CLIENT_DEFAULT,
        )
        return self._handle_data_response(response)

    async def list_uploads(
        self,
        ids: Iterable[str] | None = None,
        query: str | None = None,
        fields: Mapping[str, Mapping[str, str]] | None = None,
        order_by: str | None = None,
        locale: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> tuple[list["Upload"], int]:
        params = self._items_params(locale=locale, order_by=order_by)
        self._page_params(params, limit=limit, offset=offset)
        self._filter_params(
            params,
            ids=ids,
            query=query,
            fields=fields,
        )

        response = await self._client.request(
            "GET", "uploads", params=params, headers=self._api_headers
        )
        return self._handle_list_response(response)

    def iter_uploads(
        self,
        page_size: int = 30,
        *,
        ids: Iterable[str] | None = None,
        query: str | None = None,
        fields: Mapping[str, Mapping[str, str]] | None = None,
        order_by: str | None = None,
        locale: str | None = None,
    ) -> AsyncGenerator["Upload", None]:
        return self._iter_paginated(
            self.list_uploads,
            page_size,
            order_by=order_by,
            locale=locale,
            ids=ids,
            query=query,
            fields=fields,
        )

    async def get_referenced_records_by_upload(
        self,
        id: str,
        nested: bool = False,
        version: "Optional[AnyVersion]" = None,
    ) -> list["Record"]:
        response = await self._client.request(
            "GET",
            f"uploads/{id}/references",
            headers=self._api_headers,
            params=self._records_params(nested=nested, version=version),
        )
        return self._handle_data_response(response)

    async def create_tag(self, name: str) -> str:
        response = await self._client.request(
            "POST",
            "upload-tags",
            headers=self._upload_headers,
            json=self._api_params("upload_tag", name=name),
        )
        return self._handle_data_response(response)

    async def list_tags(
        self,
        tag: "TagType" = "manual",
        query: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> tuple[list["UploadTag"], int]:
        self._page_params(params := {}, offset=offset, limit=limit)
        self._filter_params(params, query=query)
        response = await self._client.request(
            "GET",
            self._tags_endpoint(tag),
            headers=self._api_headers,
            params=params,
        )
        return self._handle_list_response(response)

    def iter_tags(
        self,
        page_size: int = 30,
        *,
        tag: "TagType" = "manual",
    ) -> AsyncGenerator["UploadTag", None]:
        return self._iter_paginated(self.list_tags, page_size, tag=tag)
