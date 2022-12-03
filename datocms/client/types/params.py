from typing import Any, TypedDict, NotRequired


__all__ = ["Payload", "PayloadData", "PayloadGraphQL"]


class PayloadData(TypedDict):
    type: str
    attributes: dict[str]


class Payload(TypedDict):
    data: PayloadData


class PayloadGraphQL(TypedDict):
    query: str
    attributes: NotRequired[dict[str, Any]]
    