#!/usr/bin/env python3

""" Most of the functionality of the AnkiDataFrames is already tested in
test_core, because that saves to write a lot of duplicate code.

Everything else is tested here.
"""

# std
import pathlib
import unittest

# ours
from ankipandas.ankidf import AnkiDataFrame as AnkiDF


class TestAnkiDF(unittest.TestCase):
    def setUp(self):
        self.db_path = pathlib.Path(__file__).parent / "data" / \
                       "few_basic_cards" / "collection.anki2"

    def test_help(self):
        notes = AnkiDF.notes(self.db_path)
        hlp = notes.help()
        # todo


if __name__ == "__main__":
    unittest.main()
