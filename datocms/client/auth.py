from requests.auth import AuthBase
from requests.models import PreparedRequest
from re import fullmatch


__all__ = ["DatoAuth", "BearerAuth"]


class BearerAuth(AuthBase):
    _token: str

    def __init__(self, token: str):
        if not isinstance(token, str):
            raise TypeError("Token is not a `str`")
        self._token = token

    def __call__(self, r: PreparedRequest) -> PreparedRequest:
        r.headers["Authorization"] = f"Bearer {self._token}"
        return r


class DatoAuth(BearerAuth):
    def __init__(self, token: str):
        super().__init__(token)

        if fullmatch(r"[a-z0-9]{30}", token) is None:
            raise ValueError("Token format invalid.")
