from os import environ
from typing import cast, Any
from requests import Session, Response

from .auth import DatoAuth
from .types.response import Result


__all__ = ["ClientBase"]


class ClientBase:
    session: Session

    def __init__(self, token: str | None = None):
        self.session = session = Session()
        session.auth = DatoAuth(token or environ["DATO_API_TOKEN"])
        session.headers.update({"Accept": "application/json"})

    @classmethod
    def _handle_data_response(cls, response: Response) -> dict[str, Any]:
        response.raise_for_status()
        return cast(Result, response.json())["data"]
