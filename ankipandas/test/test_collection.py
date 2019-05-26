#!/usr/bin/env python3

# std
import pathlib
import unittest

# ours
from ankipandas.collection import Collection


class TestCollection(unittest.TestCase):
    def setUp(self):
        self.db_path = pathlib.Path(__file__).parent / "data" / \
                       "few_basic_cards" / "collection.anki2"

        self.col = Collection(self.db_path)
        self.notes = self.col.notes
        self.cards = self.col.cards
        self.revs = self.col.revs

    def test_summarize_changes_uninitialized(self):
        col = Collection(self.db_path)
        sc = col.summarize_changes(output="dict")
        self.assertEqual(len(sc), 0)

    def test_summarize_changes_no_changes(self):
        self.col.summarize_changes()
        sc = self.col.summarize_changes(output="dict")
        for item in ["cards", "revs", "notes"]:
            with self.subTest(item=item):
                self.assertEqual(sc[item]["n_modified"], 0)
                self.assertEqual(sc[item]["n_added"], 0)
                self.assertEqual(sc[item]["n_deleted"], 0)
                self.assertEqual(sc[item]["has_changed"], False)

    def test_summarize_notes_changed(self):
        col = Collection(self.db_path)
        col.notes.add_tag("this_will_be_modified", inplace=True)
        sc = col.summarize_changes(output="dict")
        self.assertEqual(sc["notes"]["n_modified"], sc["notes"]["n"])


if __name__ == "__main__":
    unittest.main()