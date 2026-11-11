# std
from __future__ import annotations

# ours
from ankipandas.util.guid import _base62, _base91, guid


def test_base62_zero_returns_first_digit():
    assert _base62(0) == "a"


def test_base91_zero_returns_first_digit():
    assert _base91(0) == "a"


def test_guid_never_empty():
    for _ in range(200):
        assert guid()
