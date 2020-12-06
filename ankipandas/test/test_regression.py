#!/usr/bin/env python3

""" These tests are created from issues that we fixed to avoid that they might
come back later.
"""

# ours
from ankipandas.collection import Collection
from ankipandas.test.util import parameterized_paths


@parameterized_paths()
def test_inplace_merge_notes(db_path):
    """ https://github.com/klieret/AnkiPandas/issues/51
    AttributeError: 'NoneType' object has no attribute 'col'
    """
    col = Collection(db_path)
    col.cards.merge_notes(inplace=True)
