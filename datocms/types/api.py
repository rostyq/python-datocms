from typing import Any, TypedDict, NotRequired, Literal, Iterable, Mapping

from httpx._types import TimeoutTypes

from .relationships import Creator, ItemType
from .locale import Localized
from .upload import Metadata


__all__ = [
    "Version",
    "AnyVersion",
    "TagType",
    "Result",
    "Payload",
    "PayloadData",
    "PayloadGraphQL",
    "PayloadUpdate",
    "RelationshipsUpdate",
    "Result",
    "ArrayResult",
    "Meta",
    "GraphqlResult",
    "GraphqlError",
    "ErrorLocation",
    "ErrorExtensions",
    "ErrorProblem",
    # Parameter TypedDicts
    "PaginationParams",
    "RetryParams",
    "ExecuteParams",
    "ListRecordsParams",
    "IterRecordsParams",
    "ListUploadsParams",
    "IterUploadsParams",
    "UploadMetadataParams",
    "UpdateUploadParams",
    "CreateUploadParams",
    "CreateUploadJobParams",
    "PollJobParams",
    "ListTagsParams",
    "IterTagsParams",
    # Union types with pagination
    "ListRecordsWithPaginationParams",
    "ListUploadsWithPaginationParams",
    "ListTagsWithPaginationParams",
    # Union types with retry parameters
    "CreateUploadWithRetryParams",
]

Version = Literal["published", "current"]
AnyVersion = Literal[Version, "published-or-current"]
TagType = Literal["manual", "smart"]


class RelationshipsUpdate(TypedDict, total=False):
    creator: Creator
    item: ItemType


class PayloadData(TypedDict):
    type: str
    attributes: dict[str, Any]


class PayloadUpdate(TypedDict):
    id: str
    type: str
    relationships: NotRequired[RelationshipsUpdate]


class Payload(TypedDict):
    data: PayloadData


class PayloadGraphQL(TypedDict):
    query: str
    attributes: NotRequired[dict[str, Any]]
    variables: NotRequired[dict[str, Any]]


class Result(TypedDict):
    data: dict[str, Any]


class Meta(TypedDict):
    total_count: int


class ArrayResult(TypedDict):
    data: list[Any]
    meta: Meta


class ErrorLocation(TypedDict):
    line: int
    column: int


class ErrorProblem(TypedDict):
    path: list[str]
    explanation: str
    message: str


class ErrorExtensions(TypedDict, total=False):
    code: str
    value: str
    typeName: str
    fieldName: str
    problems: list[ErrorProblem]


class GraphqlError(TypedDict):
    message: str
    locations: NotRequired[list[ErrorLocation]]
    path: NotRequired[list[str]]
    extensions: NotRequired[ErrorExtensions]


class GraphqlResult(TypedDict):
    data: Any
    errors: NotRequired[list[dict[str, Any]]]


class PaginationParams(TypedDict, total=False):
    limit: int | None
    offset: int | None


class RetryParams(TypedDict, total=False):
    max_retries: int
    retry_delay: float


class ExecuteParams(TypedDict, total=False):
    environment: str | None
    include_drafts: bool
    exclude_invalid: bool | None
    timeout: Any  # TimeoutTypes


class ListRecordsParams(TypedDict, total=False):
    nested: bool
    ids: Iterable[str] | None
    types: Iterable[str] | None
    query: str | None
    fields: Mapping[str, Mapping[str, str]] | None
    only_valid: bool
    locale: str | None
    order_by: str | None
    version: Version | None
    timeout: TimeoutTypes | None


class IterRecordsParams(TypedDict, total=False):
    nested: bool
    ids: Iterable[str] | None
    types: Iterable[str] | None
    query: str | None
    fields: Mapping[str, Mapping[str, str]] | None
    only_valid: bool
    locale: str | None
    order_by: str | None
    version: Version | None
    timeout: TimeoutTypes | None


class ListUploadsParams(TypedDict, total=False):
    ids: Iterable[str] | None
    query: str | None
    fields: Mapping[str, Mapping[str, str]] | None
    order_by: str | None
    locale: str | None


class IterUploadsParams(TypedDict, total=False):
    ids: Iterable[str] | None
    query: str | None
    fields: Mapping[str, Mapping[str, str]] | None
    order_by: str | None
    locale: str | None


class UploadMetadataParams(TypedDict, total=False):
    path: str | None
    basename: str | None
    copyright: str | None
    author: str | None
    notes: str | None
    metadata: Localized[Metadata]
    tags: list[str] | None


class UpdateUploadParams(UploadMetadataParams, total=False):
    creator: Any  # CreatorId
    timeout: TimeoutTypes | None


class CreateUploadJobParams(TypedDict, total=False):
    copyright: str | None
    author: str | None
    notes: str | None
    metadata: Localized[Metadata]
    tags: list[str] | None
    timeout: TimeoutTypes | None


class CreateUploadParams(CreateUploadJobParams, total=False):
    content_type: str | None


class PollJobParams(RetryParams, total=False):
    timeout: TimeoutTypes | None


class ListTagsParams(TypedDict, total=False):
    tag: TagType
    query: str | None


class IterTagsParams(TypedDict, total=False):
    tag: TagType


class ListRecordsWithPaginationParams(ListRecordsParams, PaginationParams, total=False):
    pass


class ListUploadsWithPaginationParams(ListUploadsParams, PaginationParams, total=False):
    pass


class ListTagsWithPaginationParams(ListTagsParams, PaginationParams, total=False):
    pass


class CreateUploadWithRetryParams(CreateUploadParams, RetryParams, total=False):
    pass
