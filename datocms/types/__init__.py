from typing import TypeVar, Generic, TypedDict


__all__ = ["DataField"]


T = TypeVar("T")


class DataField(TypedDict, Generic[T]):
    data: T
