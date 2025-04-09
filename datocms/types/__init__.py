from typing import TypeVar, Generic, TypedDict, Literal


T = TypeVar("T")


class DataField(TypedDict, Generic[T]):
    data: T
