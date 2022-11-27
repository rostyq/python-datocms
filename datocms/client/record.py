from typing import Literal, Generator
from urllib.parse import urljoin

from .api import ClientAPI
from ..record.types import Record


__all__ = ["ClientRecord"]


class ClientRecord(ClientAPI):
    items_endpoint = urljoin(ClientAPI.api_base, "items")

    def list_records(
        self,
        nested: bool = False,
        ids: str | None = None,
        type: str | None = None,
        query: str | None = None,
        fields: str | None = None,
        locale: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        order_by: str | None = None,
        version: Literal["published", "current"] = "published",
    ) -> tuple[list[Record], int]:
        params = self._page_params(offset, limit) | self._filter_params(
            ids=ids, type=type, query=query, fields=fields
        )

        if nested is True:
            params["nested"] = "true"
        if locale is not None:
            params["locale"] = locale
        if order_by is not None:
            params["order_by"] = order_by
        if version is not None:
            params["version"] = version

        response = self.session.get(
            self.items_endpoint, params=params, headers=self._api_headers()
        )
        return self._handle_list_response(response)

    def iter_records(
        self,
        nested: bool | None = None,
        ids: str | None = None,
        type: str | None = None,
        query: str | None = None,
        fields: str | None = None,
        locale: str | None = None,
        page: int | None = None,
        order_by: str | None = None,
        version: Literal["published", "current"] = "published",
    ) -> Generator[Record, None, None]:
        return self._iter_paginated(
            self.list_records,
            page=page,
            nested=nested,
            type=type,
            order_by=order_by,
            locale=locale,
            ids=ids,
            query=query,
            fields=fields,
            version=version,
        )
