from .api import ClientAPI
from ..model.types import Model


__all__ = ["ClientModel"]


class ClientModel(ClientAPI):
    item_types_endpoint = ClientAPI.urljoin("item-types")

    def list_models(self) -> list[Model]:
        response = self.session.get(self.item_types_endpoint, headers=self._api_headers())
        response.raise_for_status()
        return response.json()["data"]