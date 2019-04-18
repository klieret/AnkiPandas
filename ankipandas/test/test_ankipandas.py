#!/usr/bin/env python3

# std
import unittest
import pathlib

# ours
from ankipandas.function_interface import get_cards_df, find_database


class TestDbFinder(unittest.TestCase):
    def setUp(self):
        self.basepath = pathlib.Path(__file__).parent / "data"

    def testFindDb(self):
        self.assertEqual(
            str(find_database(self.basepath, "few_basic_cards").relative_to(self.basepath)),
            "few_basic_cards/collection.anki2"
        )


class TestGetCardsDf(unittest.TestCase):
    def setUp(self):
        self.db_path = pathlib.Path(__file__).parent / "data" / "few_basic_cards" / "collection.anki2"

    def testGetCardsDf(self):
        df = get_cards_df(self.db_path)
        self.assertEqual(len(df), 3)
