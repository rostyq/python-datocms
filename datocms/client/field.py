from typing import Any
from .api import ClientAPI


__all__ = ["ClientField"]


class ClientField(ClientAPI):
    fields_endpoint = ClientAPI.urljoin("fields/{id}")
    item_fields_endpoint = ClientAPI.urljoin("item-types/{id}/fields")

    def list_fields(self, id: str) -> list[Any]:
        response = self.session.get(self.item_fields_endpoint.format(id=id), headers=self._api_headers())
        response.raise_for_status()
        return response.json()["data"]