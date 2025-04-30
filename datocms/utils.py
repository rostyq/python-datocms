from typing import TYPE_CHECKING
from base64 import urlsafe_b64decode
from uuid import UUID

if TYPE_CHECKING:
    from .types.relationships import ItemId


def unpadded_urlsafe_b64decode(s: str) -> bytes:
    return urlsafe_b64decode(s.ljust((ls := len(s)) + (-ls % 4), "="))


def validate_item_id(s: str, /) -> "ItemId":
    if s.isdigit():
        if int(s) > 281474976710655:
            raise ValueError("Integer ID exceeds the maximum allowed value")
    elif UUID(bytes=unpadded_urlsafe_b64decode(s)).version != 4:
        raise ValueError("Invalid UUID version (must be version 4)")

    return s
