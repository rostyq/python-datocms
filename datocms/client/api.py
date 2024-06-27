from typing import cast
from urllib.parse import urljoin
from requests import Response
from typing import Callable, Protocol, Generic, TypeVar, Generator

from .base import ClientBase
from .types import query
from .types.params import PayloadData, Payload, PayloadUpdate
from .types.response import ArrayResult


__all__ = ["ClientAPI"]


T = TypeVar("T")


class GetPage(Protocol, Generic[T]):
    def __call__(self, limit: int, offset: int, **kwargs) -> tuple[list[T], int]:
        ...


class ClientAPI(ClientBase):
    api_base = "https://site-api.datocms.com"

    @classmethod
    def urljoin(cls, url: str, allow_fragments: bool = True):
        return urljoin(cls.api_base, url, allow_fragments=allow_fragments)

    @staticmethod
    def _api_headers() -> dict:
        return {"X-Api-Version": "3"}

    @staticmethod
    def _page_params(
        offset: int | None = None, limit: int | None = None
    ) -> query.Page:
        params = {}
        if offset is not None:
            params["page[offset]"] = offset
        if limit is not None:
            params["page[limit]"] = limit
        return params

    @staticmethod
    def _filter_params(
        ids: str | None = None,
        type: str | None = None,
        query: str | None = None,
        fields: str | None = None,
    ) -> query.Filter:
        params = {}
        if ids is not None:
            params["filter[ids]"] = ids
        if type is not None:
            params["filter[type]"] = type
        if query is not None:
            params["filter[query]"] = query
        if fields is not None:
            params["filter[fields]"] = fields
        return params

    @staticmethod
    def _api_payload(data: PayloadData):
        return Payload(data=data)

    @classmethod
    def _api_parameters(cls, type: str, **attributes) -> Payload:
        return cls._api_payload(PayloadData(type=type, attributes=attributes))

    @classmethod
    def _api_update(cls, id: str, type: str, **kwargs) -> Payload:
        return cls._api_payload(PayloadUpdate(id=id, type=type) | kwargs)

    @staticmethod
    def _list_result_to_tuple(result: ArrayResult) -> tuple[list[T], int]:
        return result["data"], result["meta"]["total_count"]

    @classmethod
    def _handle_list_response(cls, response: Response) -> tuple[list[T], int]:
        response.raise_for_status()
        return cls._list_result_to_tuple(response.json())

    @staticmethod
    def _iter_paginated(
        func: GetPage[T], page: int | None, **kwargs
    ) -> Generator[T, None, None]:
        offset: int = 0
        total: int = 1

        get: Callable[[int], tuple[list[T], int]] = lambda offset: func(
            limit=page, offset=offset, **kwargs
        )

        while offset < total:
            items, total = get(offset)
            offset += len(items)

            for item in items:
                yield item