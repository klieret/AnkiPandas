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
from ankipandas.data.columns import columns
from ankipandas.core_functions import get_notes, check_dnames_did, load_db


class TestAnkiDF(unittest.TestCase):
    def setUp(self):
        self.db_path = pathlib.Path(__file__).parent / "data" / \
                       "few_basic_cards" / "collection.anki2"
        self.db = load_db(self.db_path)

    def test_merge_note_info(self):
        merged = AnkiDF.cards(self.db_path).merge_notes()
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(list(
                set(columns["cards"]) | set(columns["notes"]) |
                {"ndata", "nflags", "nmod", "nusn"}  # clashes
            ))
        )

    def test_merge_card_info(self):
        merged = AnkiDF.revs(self.db_path).merge_cards()
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(list(
                set(columns["revlog"]) | set(columns["cards"]) |
                {"civl", "ctype", "cusn", "cid", "cfactor"}  # clashes
            ))
        )

    def test_add_nids(self):
        cards = AnkiDF.cards(self.db_path).add_nids()
        self.assertIn("nid", list(cards.columns))
        self.assertListEqual(
            sorted(list(cards["nid"].unique())),
            sorted(list(get_notes(self.db)["id"].unique()))
        )

    def test_add_mids(self):
        notes = AnkiDF.notes(self.db_path).add_mids()
        self.assertEqual(
            len(notes["mid"].unique()),
            2  # we don't have notesfor every model
        )

    def test_add_mnames(self):
        # todo: add_mids() should soon be called automatically
        notes = AnkiDF.notes(self.db_path).add_mnames()
        self.assertEqual(
            sorted(list(notes["mname"].unique())),
            ["Basic", 'Basic (and reversed card)']
        )

    def test_add_dnames(self):
        cards = AnkiDF.cards(self.db_path).add_dnames()
        self.assertEqual(
            sorted(list(cards["dname"].unique())),
            ["Default"]
        )
        self.assertTrue(
            check_dnames_did(self.db, cards)
        )

    def test_add_fields_as_columns(self):
        # todo: add_mnames shouldn't be necessary
        notes = AnkiDF.notes(self.db_path).add_mnames().add_fields_as_columns()
        self.assertEqual(
            sorted(list(notes.columns)),
            sorted(columns["notes"] + ["mname", "Front", "Back"])
        )
        self.assertEqual(
            list(notes.query("mname=='Basic'")["Front"].unique()),
            ["Basic: Front"]
        )

    def test_fields_as_columns_to_flds(self):
        # Add fields as column, remove original 'flds' column, then
        # add it back from the field columns and see if things still check
        # out
        notes = AnkiDF.notes(self.db_path).add_fields_as_columns()
        print("####")
        print(notes)
        print("#####")
        flds = copy.copy(notes["flds"].values)
        notes["flds"] = ""
        notes.fields_as_columns_to_flds(inplace=True, drop=True)
        self.assertEqual(
            list(flds),
            list(notes["flds"].values)
        )
        self.assertListEqual(
            sorted(list(notes.columns)),
            sorted(columns["notes"])
        )

    def test_fields_as_columns_to_flds_2(self):
        notes = AnkiDF.notes(self.db_path).add_fields_as_columns(prepend="fld_")
        flds = copy.deepcopy(notes["flds"].values)
        notes["flds"] = ""
        notes = notes.fields_as_columns_to_flds(drop=True, prepended="fld_")
        self.assertListEqual(
            list(flds),
            list(notes["flds"].values)
        )

    def test_help(self):
        notes = AnkiDF.notes(self.db_path)
        hlp = notes.help()
        # todo

if __name__ == "__main__":
    unittest.main()
