from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .types.errors import ErrorAttributes, ErrorCodeType
    from .types.api import (
        GraphqlError,
        ErrorLocation,
        ErrorExtensions,
    )


__all__ = [
    "DatoError",
    "DatoGraphqlError",
    "DatoApiError",
    "GraphqlError",
]


class DatoError(Exception):
    def __init__(self, *args):
        super().__init__(*args)

    @classmethod
    def from_dict(cls, data: dict[str, Any], /):
        raise NotImplementedError(
            f"{cls.__name__}.from_dict() must be implemented in subclasses"
        )


class DatoGraphqlError(DatoError):
    def __init__(
        self,
        message: str,
        locations: Optional[list["ErrorLocation"]] = None,
        path: list[str] | None = None,
        extensions: "Optional[ErrorExtensions]" = None,
    ):
        super().__init__()
        self.message = message
        self.locations = locations
        self.path = path
        self.extensions = extensions

    @classmethod
    def from_dict(cls, data: "GraphqlError", /):
        return cls(
            message=data.get("message") or "",
            locations=data.get("locations"),
            path=data.get("path"),
            extensions=data.get("extensions"),
        )

    def _fmt_locs(self) -> str:
        if self.locations is None:
            return ""
        elif len(self.locations) == 1:
            loc = self.locations[0]
            return f"line {loc['line']}, column {loc['column']}"
        else:
            return ", ".join(f"{loc['line']}:{loc['column']}" for loc in self.locations)

    def _fmt_path(self) -> str:
        return ".".join(self.path) if self.path else ""

    def _fmt_err(self) -> str:
        return f"{self.message} at ({self._fmt_locs()})"

    def __str__(self):
        message_array = [self.message]
        if self.locations is not None:
            message_array.extend(["at", self._fmt_locs()])
        if self.path is not None:
            message_array.extend(["in", self._fmt_path()])
        return " ".join(message_array)


class DatoApiError(DatoError):
    code: "ErrorCodeType"

    def __init__(
        self,
        code: "ErrorCodeType",
        doc_url: str,
        details: dict[str, Any],
        transient: bool,
    ):
        super().__init__()
        self.code = code
        self.doc_url = doc_url
        self.details = details
        self.transient = transient

    @classmethod
    def from_dict(cls, data: "ErrorAttributes", /):
        return cls(
            code=data["code"],
            doc_url=data["doc_url"],
            details=data["details"],
            transient=data.get("transient", False),
        )

    def __str__(self) -> str:
        return f"{self.code}{': %s' % self.details if self.details else ''}. See {self.doc_url} for more details."
