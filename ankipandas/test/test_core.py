#!/usr/bin/env python3

# std
import unittest
import pathlib

# ours
from ankipandas.core_functions import *


class TestCoreFunctions(unittest.TestCase):
    def setUp(self):
        self.db = load_db(
            pathlib.Path(__file__).parent / "data" / "few_basic_cards" / "collection.anki2"
        )

    def tearDown(self):
        close_db(self.db)

    def test_get_cards(self):
        cards = get_cards(self.db)
        self.assertEqual(len(cards), 3)
        self.assertEqual(
            list(sorted(cards.columns)),
            sorted([
                'id',
                'nid',
                'did',
                'ord',
                'mod',
                'usn',
                'type',
                'queue',
                'due',
                'ivl',
                'factor',
                'reps',
                'lapses',
                'left',
                'odue',
                'odid',
                'flags',
                'data'
            ])
        )

    def test_get_notes(self):
        notes = get_notes(self.db)
        self.assertEqual(len(notes), 2)
        self.assertEqual(
            list(sorted(notes.columns)),
            sorted([
                'id',
                'guid',
                'mid',
                'mod',
                'usn',
                'tags',
                'flds',
                'sfld',
                'csum',
                'flags',
                'data',
            ])
        )

    def test_get_revlog(self):
        revlog = get_revlog(self.db)
        # todo assert length
        self.assertEqual(
            list(sorted(revlog.columns)),
            sorted([
                'id',
                'cid',
                'usn',
                'ease',
                'ivl',
                'lastIvl',
                'factor',
                'time',
                'type'
            ])
        )

    def test_get_deck_info(self):
        dinfo = get_deck_info(self.db)
        # todo

    def test_get_deck_names(self):
        names = get_deck_names(self.db)
        self.assertDictEqual(
            names,
            {"1": "Default"}
        )

    def test_get_model_info(self):
        minfo = get_model_info(self.db)
        # todo



if __name__ == "__main__":
    unittest.main()