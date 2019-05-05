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
import ankipandas.core_functions as core


# todo: add more notes to test deck
class TestAnkiDF(unittest.TestCase):
    def setUp(self):
        self.db_path = pathlib.Path(__file__).parent / "data" / \
                       "few_basic_cards" / "collection.anki2"
        self.db = core.load_db(self.db_path)

    # Test constructors
    # ==========================================================================

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

    # Test properties
    # ==========================================================================

    # Trivial cases
    # --------------------------------------------------------------------------

    def test_nids_notes(self):
        notes = AnkiDF.notes(self.db_path)
        self.assertIn("nid", list(notes.columns))
        self.assertListEqual(
            list(notes["nid"]),
            list(notes.nid)
        )
        self.assertListEqual(
            list(notes["nid"].unique()),
            list(map(str, core.get_table(self.db, "notes")["id"].unique()))
        )
        self.assertEqual(
            len(notes.nid.unique()),
            len(notes.nid)
        )

    def test_cids_cards(self):
        cards = AnkiDF.cards(self.db_path)
        self.assertIn("cid", list(cards.columns))
        self.assertListEqual(
            list(cards["cid"]),
            list(cards.cid)
        )
        self.assertListEqual(
            list(cards["cid"].unique()),
            list(map(str, core.get_table(self.db, "cards")["id"].unique()))
        )
        self.assertEqual(
            len(cards.cid.unique()),
            len(cards.cid)
        )

    def test_rids_revs(self):
        revs = AnkiDF.revs(self.db_path)
        self.assertIn("rid", list(revs.columns))
        self.assertListEqual(
            list(revs["rid"]),
            list(revs.rid)
        )
        self.assertListEqual(
            list(revs["rid"].unique()),
            list(map(str, core.get_table(self.db, "revs")["id"].unique()))
        )
        self.assertEqual(
            len(revs.rid.unique()),
            len(revs.rid)
        )

    # Slightly more elaborate cases
    # --------------------------------------------------------------------------

    def test_nids_cards(self):
        cards = AnkiDF.cards(self.db_path)
        notes = AnkiDF.notes(self.db_path)
        self.assertListEqual(
            sorted(list(cards.nid.unique())),
            sorted(list(notes.nid.unique()))
        )

    def test_nids_revs(self):
        revs = AnkiDF.revs(self.db_path)
        notes = AnkiDF.notes(self.db_path)
        self.assertListEqual(
            sorted(list(revs.nid.unique())),
            sorted(list(notes.nid.unique()))
        )

    def test_nids_nexist(self):
        nexist = AnkiDF()
        with self.assertRaises(ValueError):
            # noinspection PyStatementEffect
            nexist.nid

    def test_cids_revs(self):
        revs = AnkiDF.revs(self.db_path)
        cards = AnkiDF.cards(self.db_path)
        self.assertListEqual(
            sorted(list(revs.cid.unique())),
            sorted(list(cards.cid.unique()))
        )

    def test_cids_notes(self):
        notes = AnkiDF.notes(self.db_path)
        with self.assertRaises(ValueError):
            # noinspection PyStatementEffect
            notes.cid

    # --------------------------------------------------------------------------

    def test_mids(self):
        mids2s = {
            "notes": set(AnkiDF.notes(self.db_path).mid),
            "cards": set(AnkiDF.cards(self.db_path).mid),
            "revs": set(AnkiDF.revs(self.db_path).mid)
        }
        mids = set(core.get_model_names(self.db).keys())
        for table, mids2 in mids2s.items():
            with self.subTest(table=table):
                self.assertTrue(mids2.issubset(mids))

    def test_dids(self):
        did2s = {
            "cards": set(AnkiDF.cards(self.db_path).did),
            "revs": set(AnkiDF.revs(self.db_path).did)
        }
        dids = set(core.get_deck_names(self.db).keys())
        for table, dids2 in did2s.items():
            with self.subTest(table=table):
                self.assertTrue(dids2.issubset(dids))

    # ==========================================================================

    def test_merge_card_info(self):
        merged = AnkiDF.revs(self.db_path).merge_cards()
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(list(
                set(our_columns["revs"]) | set(our_columns["cards"])
            ))
        )

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
