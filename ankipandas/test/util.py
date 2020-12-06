#!/usr/bin/env python3

# std
import pathlib

# 3rd
import pytest


_test_db_paths = [
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "few_basic_cards"
    / "collection.anki2",
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "few_basic_cards"
    / "collection_v1.anki2",
]


def parameterized_paths():
    return pytest.mark.parametrize("db_path", _test_db_paths)
