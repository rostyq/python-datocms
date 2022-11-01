from typing import TypedDict, Literal

from .nodes import Root


__all__ = ["Dast"]


class Dast(TypedDict):
    scheme: Literal["dast"]
    document: Root
