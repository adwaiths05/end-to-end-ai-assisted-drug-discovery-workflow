from __future__ import annotations


def split_valid_invalid(values: list[tuple[str, bool]]) -> tuple[list[str], list[str]]:
    valid = [value for value, ok in values if ok]
    invalid = [value for value, ok in values if not ok]
    return valid, invalid

