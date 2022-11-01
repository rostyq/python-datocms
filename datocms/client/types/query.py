from typing import TypedDict


__all__ = ["Page", "Filter"]


Page = TypedDict(
    "Page", {"page[limit]": int, "page[offset]": int}, total=False
)

Filter = TypedDict(
    "Filter",
    {
        "filter[ids]": str,
        "filter[type]": str,
        "filter[query]": str,
        "filter[fields]": str,
    },
    total=False,
)
