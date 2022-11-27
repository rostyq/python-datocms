from typing import Generator, Literal

from .api import ClientAPI
from ..upload_tag.types import UploadTag


__all__ = ["ClientUploadTag"]


class ClientUploadTag(ClientAPI):
    upload_tags_endpoint = ClientAPI.urljoin("upload-tags")
    upload_smart_tags_endpoint = ClientAPI.urljoin("upload-smart-tags")

    upload_tags_endpoints: dict[Literal["manual", "smart"], str] = {
        "manual": upload_tags_endpoint,
        "smart": upload_smart_tags_endpoint,
    }

    def list_tags(
        self,
        type: Literal["manual", "smart"] = "manual",
        query: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ) -> tuple[list[UploadTag], int]:
        response = self.session.get(
            self.upload_tags_endpoints.get(type, self.upload_tags_endpoint),
            params=self._page_params(offset, limit) | self._filter_params(query=query),
            headers=self._api_headers(),
        )
        return self._handle_list_response(response)

    def iter_tags(
        self,
        type: Literal["manual", "smart"] = "manual",
        page: int | None = None,
    ) -> Generator[UploadTag, None, None]:
        return self._iter_paginated(self.list_tags, page=page, type=type)

    def create_tag(self, name: str) -> str:
        response = self.session.post(
            self.upload_tags_endpoint,
            headers=self._api_headers() | self._upload_headers(),
            json=self._api_parameters("upload_tag", name=name),
        )
        return self._handle_data_response(response)
