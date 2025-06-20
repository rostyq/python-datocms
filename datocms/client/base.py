from typing import (
    TYPE_CHECKING,
    TypeVar,
    Iterable,
    AsyncIterable,
    Protocol,
    Any,
    Optional,
    MutableMapping,
    Mapping,
    Unpack,
    Union,
    Awaitable,
    cast,
)
from os import PathLike
from abc import abstractmethod

from httpx import Response

from ..errors import DatoApiError, DatoGraphqlError
from .auth import DatoAuth


if TYPE_CHECKING:
    from httpx._types import TimeoutTypes

    from ..types.api import (
        AnyVersion,
        TagType,
        Payload,
        PayloadGraphQL,
        ArrayResult,
        GraphqlResult,
        GraphqlError,
        ExecuteParams,
        CreateUploadJobParams,
        PollJobParams,
        ListRecordsWithPaginationParams,
        ListUploadsWithPaginationParams,
        ListTagsWithPaginationParams,
        ListTagsWithPaginationParams,
        ListUploadCollectionsParams,
        CreateUploadWithRetryParams,
        GetReferencedRecordsByUploadParams,
        CreateTagParams,
        UpdateUploadParams,
    )
    from ..types.errors import Error
    from ..types.record import Record
    from ..types.model import Model
    from ..types.upload import (
        Metadata,
        Upload,
        Localized,
        UploadPermission,
        UploadTag,
        UploadCollection,
    )
    from ..types.job import Job

    class GetPage[T](Protocol):
        def __call__(
            self, offset: int, *, limit: int | None
        ) -> tuple[list[T], int]: ...

    class GetPageAsync[T](Protocol):
        async def __call__(
            self, offset: int, *, limit: int | None
        ) -> tuple[list[T], int]: ...

    R = TypeVar("R")
    Returnable = Union[R, Awaitable[R]]


__all__ = [
    "DatoAuth",
    "BaseClient",
    "DEFAULT_RETRY_DELAY",
    "DEFAULT_MAX_RETRIES",
    "DatoApiError",
    "DatoGraphqlError",
]


DEFAULT_RETRY_DELAY = 1.0
DEFAULT_MAX_RETRIES = 10


class BaseClient:
    base_url: str = "https://site-api.datocms.com"
    graphql_url: str = "https://graphql.datocms.com"

    _api_headers = {"X-Api-Version": "3", "Accept": "application/json"}
    _upload_headers = {**_api_headers, "Content-Type": "application/vnd.api+json"}

    _auth: DatoAuth

    def __init__(self, token: str | None = None):
        self._auth = DatoAuth(token)

    @staticmethod
    def _handle_response(response: "Response") -> dict[str, Any]:
        result = (
            response.json()
            if "application/json" in response.headers["Content-Type"]
            else None
        )

        if response.is_success:
            return cast(dict[str, Any], result)
        elif result is not None and isinstance(data := result["data"], list):
            data: list["Error"]
            errors = [DatoApiError.from_dict(item["attributes"]) for item in data]
            if len(errors) == 1:
                raise errors[0]
            else:
                raise ExceptionGroup(",".join(error.code for error in errors), errors)
        else:
            response.raise_for_status()
            raise

    @staticmethod
    def _handle_graphql_response(response: "Response") -> dict[str, Any] | None:
        result: "GraphqlResult" = response.raise_for_status().json()
        if (errors := result.get("errors")) is None:
            return result.get("data")
        else:
            errors = [
                DatoGraphqlError.from_dict(cast("GraphqlError", error))
                for error in errors
            ]
            if len(errors) == 1:
                raise errors[0]
            else:
                raise ExceptionGroup("GraphQL errors", errors)

    @classmethod
    def _handle_data_response(cls, response: "Response") -> Any:
        return cls._handle_response(response)["data"]

    @classmethod
    def _handle_list_response(cls, response: "Response") -> tuple[list[Any], int]:
        return cls._list_result_to_tuple(
            cast("ArrayResult", cls._handle_response(response))
        )

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
        version: "Optional[AnyVersion]" = None,
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
    def _upload_relationships(
        collection_id: str | None = None,
        creator: Any | None = None,
    ):
        relationships = {}
        if collection_id is not None:
            relationships["upload_collection"] = {
                "data": {"id": collection_id, "type": "upload_collection"}
            }
        if creator is not None:
            relationships["creator"] = {"data": creator}
        return relationships

    @staticmethod
    def _api_params(name: str, /, **attributes) -> "Payload":
        return {"data": {"type": name, "attributes": attributes}}

    @staticmethod
    def _api_update(id: str, name: str, **kwargs):
        return {"data": {"id": id, "type": name, **kwargs}}

    @staticmethod
    def _list_result_to_tuple(result: "ArrayResult") -> tuple[list[Any], int]:
        return result["data"], result["meta"]["total_count"]

    @staticmethod
    def _graphql_payload(
        query: str, variables: Mapping[str, Any] | None = None
    ) -> "PayloadGraphQL":
        payload: "PayloadGraphQL" = {"query": query}
        if variables is not None and len(variables) != 0:
            payload["variables"] = dict(variables)
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

    @abstractmethod
    def execute(
        self,
        query: str,
        variables: Mapping[str, Any] | None = None,
        **kwargs: "Unpack[ExecuteParams]",
    ) -> "Returnable[dict[str, Any] | None]": ...

    @abstractmethod
    def execute_from_file(
        self,
        path: "PathLike",
        variables: "dict[str, Any] | None" = None,
        **kwargs: "Unpack[ExecuteParams]",
    ) -> "Returnable[dict[str, Any] | None]": ...

    @abstractmethod
    def list_fields(
        self, id: str, *, timeout: "Optional[TimeoutTypes]" = None
    ) -> "Returnable[list]": ...

    @abstractmethod
    def get_job_result(
        self, id: str, *, timeout: "Optional[TimeoutTypes]" = None
    ) -> "Returnable[tuple[int, Optional[Model]]]": ...

    @abstractmethod
    def poll_job(
        self, id: str, **kwargs: "Unpack[PollJobParams]"
    ) -> "Returnable[Model]": ...

    @abstractmethod
    def list_models(
        self, *, timeout: "Optional[TimeoutTypes]" = None
    ) -> "Returnable[list[Model]]": ...

    @abstractmethod
    def list_records(
        self,
        **kwargs: "Unpack[ListRecordsWithPaginationParams]",
    ) -> "Returnable[tuple[list[Record], int]]": ...

    @abstractmethod
    def request_upload_permission(
        self,
        filename: str,
        timeout: "Optional[TimeoutTypes]" = None,
    ) -> "Returnable[UploadPermission]": ...

    @abstractmethod
    def create_upload_job(
        self,
        path: str,
        **kwargs: "Unpack[CreateUploadJobParams]",
    ) -> "Returnable[Job]": ...

    @abstractmethod
    def create_upload(
        self,
        filename: str,
        content: "bytes | Iterable[bytes] | AsyncIterable[bytes]",
        **kwargs: "Unpack[CreateUploadWithRetryParams]",
    ) -> "Returnable[Model]": ...

    @abstractmethod
    def get_upload(
        self, id: str, timeout: "Optional[TimeoutTypes]" = None
    ) -> "Returnable[Upload]": ...

    @abstractmethod
    def delete_upload(
        self, id: str, timeout: "Optional[TimeoutTypes]" = None
    ) -> "Returnable[Upload]": ...

    @abstractmethod
    def list_uploads(
        self,
        **kwargs: "Unpack[ListUploadsWithPaginationParams]",
    ) -> "Returnable[tuple[list[Upload], int]]": ...

    @abstractmethod
    def get_referenced_records_by_upload(
        self,
        id: str,
        **kwargs: "Unpack[GetReferencedRecordsByUploadParams]",
    ) -> "Returnable[list[Record]]": ...

    @abstractmethod
    def create_tag(self, **kwargs: "Unpack[CreateTagParams]") -> "Returnable[str]": ...

    @abstractmethod
    def list_tags(
        self,
        **kwargs: "Unpack[ListTagsWithPaginationParams]",
    ) -> "Returnable[tuple[list[UploadTag], int]]": ...

    @abstractmethod
    def update_upload(
        self,
        id: str,
        **kwargs: "Unpack[UpdateUploadParams]",
    ) -> "Returnable[Job]": ...

    @abstractmethod
    def list_upload_collections(
        self,
        **kwargs: "Unpack[ListUploadCollectionsParams]",
    ) -> "Returnable[list[UploadCollection]]": ...
