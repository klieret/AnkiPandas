#!/usr/bin/env python3

""" Most of the functionality of the AnkiDataFrames is already tested in
test_core, because that saves to write a lot of duplicate code.

Everything else is tested here.
"""

# std
import pathlib
import unittest
import copy

# ours
from ankipandas.ankidf import AnkiDataFrame as AnkiDF
from ankipandas.data.columns import our_columns
from ankipandas.core_functions import check_decks_did, load_db


# todo: add more notes to test deck
class TestAnkiDF(unittest.TestCase):
    def setUp(self):
        self.db_path = pathlib.Path(__file__).parent / "data" / \
                       "few_basic_cards" / "collection.anki2"
        self.db = load_db(self.db_path)

    def test_tags(self):
        notes = AnkiDF.notes(self.db_path)
        self.assertListEqual(
            list(notes.query("nid=='1555579337683'")["ntags"].values)[0],
            ['other_test_tag']
        )
        self.assertListEqual(
            list(notes.query("nid=='1555579352896'")["ntags"].values)[0],
            ['some_test_tag']
        )

    def test_merge_note_info(self):
        merged = AnkiDF.cards(self.db_path).merge_notes()
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(list(
                set(our_columns["cards"]) | set(our_columns["notes"])
            ))
        )

    def test_merge_card_info(self):
        merged = AnkiDF.revs(self.db_path).merge_cards()
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(list(
                set(our_columns["revs"]) | set(our_columns["cards"])
            ))
        )

    # def test_add_nids(self):
    #     cards = AnkiDF.cards(self.db_path).add_nids()
    #     self.assertIn("nid", list(cards.columns))
    #     self.assertListEqual(
    #         sorted(list(cards["nid"].unique())),
    #         sorted(list(get_notes(self.db)["id"].unique()))
    #     )

    # def test_add_mids(self):
    #     notes = AnkiDF.notes(self.db_path).add_mids()
    #     self.assertEqual(
    #         len(notes["mid"].unique()),
    #         2  # we don't have notesfor every model
    #     )

    # def test_add_models(self):
    #     # todo: add_mids() should soon be called automatically
    #     notes = AnkiDF.notes(self.db_path).add_models()
    #     self.assertEqual(
    #         sorted(list(notes["model"].unique())),
    #         ["Basic", 'Basic (and reversed card)']
    #     )

    # def test_add_decks(self):
    #     cards = AnkiDF.cards(self.db_path).add_decks()
    #     self.assertEqual(
    #         sorted(list(cards["deck"].unique())),
    #         ["Default"]
    #     )
    #     self.assertTrue(
    #         check_decks_did(self.db, cards)
    #     )

    def test_fields_as_columns(self):
        notes = AnkiDF.notes(self.db_path).fields_as_columns()
        cols = our_columns["notes"].copy()
        cols.remove("nflds")
        prefix = notes.fields_as_columns_prefix
        new_cols = [
            prefix + item
            for item in ["Front", "Back"]
        ]
        self.assertEqual(
            sorted(list(notes.columns)),
            sorted(cols + new_cols)
        )
        # fixme: put pack
        # self.assertEqual(
        #     list(notes.query("model=='Basic'")[prefix + "Front"].unique()),
        #     ["Basic: Front"]
        # )

    def test_fields_as_list(self):
        # Add fields as column, remove original 'flds' column, then
        # add it back from the field columns and see if things still check
        # out
        notes = AnkiDF.notes(self.db_path)
        flds = copy.copy(notes["nflds"].values)
        notes.fields_as_columns(inplace=True)
        notes.fields_as_list(inplace=True)
        self.assertEqual(
            list(flds),
            list(notes["nflds"].values)
        )
        self.assertListEqual(
            sorted(list(notes.columns)),
            sorted(our_columns["notes"])
        )

    def test_help(self):
        notes = AnkiDF.notes(self.db_path)
        hlp = notes.help()
        # todo


if __name__ == "__main__":
    unittest.main()
