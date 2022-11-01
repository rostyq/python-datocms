from typing import Literal, TypedDict
from .relationships import FieldSetId


__all__ = ["Field"]


class Attributes(TypedDict):
    label: str
    field_type: str
    api_key: str
    localized: bool
    validators: dict
    appearance: dict
    position: int
    hint: str | None
    default_value: bool | None | str | int | float | object


class FieldSet(TypedDict):
    data: FieldSetId


class Relationships(TypedDict):
    fieldset: FieldSet


class Field(TypedDict):
    type: Literal["field"]
    attributes: Attributes
    relationships: Relationships