from os import environ
from httpx import Auth, Request


__all__ = ["DatoAuth"]


class DatoAuth(Auth):
    def __init__(self, token: str | None = None, /):
        self._token = token or environ["DATOCMS_API_TOKEN"]

    def auth_flow(self, request: Request):
        request.headers["Authorization"] = f"Bearer {self._token}"
        yield request
