from typing import Any, TypedDict


__all__ = ["Result", "ArrayResult", "Meta"]


class Result(TypedDict):
    data: dict[str, Any]


class Meta(TypedDict):
    total_count: int


class ArrayResult(TypedDict):
    data: list[Any]
    meta: Meta