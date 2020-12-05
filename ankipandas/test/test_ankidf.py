#!/usr/bin/env python3

""" Most of the functionality of the AnkiDataFrames is already tested in
test_core, because that saves to write a lot of duplicate code.

Everything else is tested here.
"""

# std
import pathlib
import unittest
import copy

# 3rd
import numpy as np

# ours
from ankipandas.ankidf import AnkiDataFrame as AnkiDF
from ankipandas._columns import our_columns
import ankipandas.raw as raw
from ankipandas.collection import Collection
import ankipandas._columns as _columns
from ankipandas.util.log import set_debug_log_level


class TestAnkiDF(unittest.TestCase):
    db_path = (
        pathlib.Path(__file__).parent
        / "data"
        / "few_basic_cards"
        / "collection.anki2"
    )

    def setUp(self):
        set_debug_log_level()
        self.db = raw.load_db(self.db_path)

        self.col = Collection(self.db_path)

        # Do not modify this one!
        self.notes = self.col.notes
        self.cards = self.col.cards
        self.revs = self.col.revs
        self.table2adf = {
            "notes": self.notes,
            "cards": self.cards,
            "revs": self.revs,
        }
        self.adfs = [self.notes, self.cards, self.revs]

        self.empty_notes = self.col.empty_notes()
        self.empty_cards = self.col.empty_cards()
        self.empty_revs = self.col.empty_revs()

    def nnotes(self):
        return self.notes.copy()

    def ncards(self):
        return self.cards.copy()

    def nrevs(self):
        return self.revs.copy()

    def nenotes(self):
        return self.empty_notes.copy()

    def necards(self):
        return self.empty_cards.copy()

    def nerevs(self):
        return self.empty_revs.copy()

    def ntable(self, table):
        if table == "notes":
            return self.nnotes()
        elif table == "cards":
            return self.ncards()
        elif table == "revs":
            return self.nrevs()
        else:
            raise ValueError("Unknown table")

    def ntable2adf(self):
        return {
            "notes": self.nnotes(),
            "cards": self.ncards(),
            "revs": self.nrevs(),
        }

    def nadfs(self):
        return [self.nnotes(), self.ncards(), self.nrevs()]

    # Test constructors
    # ==========================================================================

    def test_empty(self):
        eadfs = {
            "notes": self.col.empty_notes(),
            "cards": self.col.empty_cards(),
            "revs": self.col.empty_revs(),
        }
        for table, eadf in eadfs.items():
            self.assertEqual(len(eadf), 0)
            adf = self.table2adf[table]
            self.assertListEqual(
                sorted(list(adf.columns)), sorted(list(eadf.columns))
            )

    def test_tags(self):
        self.assertListEqual(
            list(self.notes.query("index=='1555579337683'")["ntags"].values)[0],
            ["other_test_tag"],
        )
        self.assertListEqual(
            list(self.notes.query("index=='1555579352896'")["ntags"].values)[0],
            ["some_test_tag"],
        )

    def test_cards(self):
        cards = self.cards
        self.assertGreater(len(cards), 11)
        self.assertEqual(
            list(sorted(cards.columns)), sorted(our_columns["cards"])
        )

    def test_notes(self):
        notes = self.notes
        self.assertGreater(len(notes), 6)
        self.assertEqual(
            list(sorted(notes.columns)), sorted(our_columns["notes"])
        )

    def test_get_revs(self):
        revs = self.revs
        self.assertEqual(
            list(sorted(revs.columns)), sorted(our_columns["revs"])
        )
        self.assertGreater(len(revs), 4)

    # Test merging
    # ==========================================================================

    def test_merge_notes_cards(self):
        merged = self.ncards().merge_notes()
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(list(set(our_columns["cards"]) | set(our_columns["notes"]))),
        )

    def test_merge_notes_revs(self):
        merged = self.nrevs().merge_notes()
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(
                list(
                    # Note: 'nid' is not a notes column.
                    set(our_columns["revs"])
                    | set(our_columns["notes"])
                    | {"nid"}
                )
            ),
        )

    def test_merge_notes_raises(self):
        with self.assertRaises(ValueError):
            self.nnotes().merge_notes()

    def test_merge_cards(self):
        merged = self.nrevs().merge_cards()
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(list(set(our_columns["revs"]) | set(our_columns["cards"]))),
        )

    def test_merge_cards_raises(self):
        with self.assertRaises(ValueError):
            self.ncards().merge_cards()
        with self.assertRaises(ValueError):
            self.nnotes().merge_cards()

    # Test properties
    # ==========================================================================

    # Trivial cases
    # --------------------------------------------------------------------------

    def test_nids_notes(self):
        self.assertListEqual(list(self.notes.index), list(self.notes.nid))
        self.assertListEqual(
            list(self.notes.index),
            list(raw.get_table(self.db, "notes")["id"].unique()),
        )
        self.assertEqual(len(self.notes.nid.unique()), len(self.notes.nid))

    def test_cids_cards(self):
        self.assertListEqual(list(self.cards.index), list(self.cards.cid))
        self.assertListEqual(
            list(self.cards.index),
            list(raw.get_table(self.db, "cards")["id"].unique()),
        )
        self.assertEqual(len(self.cards.cid.unique()), len(self.cards.cid))

    def test_rids_revs(self):
        self.assertListEqual(list(self.revs.index), list(self.revs.rid))
        self.assertListEqual(
            list(self.revs.index),
            list(raw.get_table(self.db, "revs")["id"].unique()),
        )
        self.assertEqual(len(self.revs.rid.unique()), len(self.revs.rid))

    # Slightly more elaborate cases
    # --------------------------------------------------------------------------

    def test_nids_cards(self):
        self.assertListEqual(
            sorted(list(self.cards.nid.unique())),
            sorted(list(self.notes.nid.unique())),
        )

    def test_nids_revs(self):
        self.assertTrue(
            set(self.notes.nid.unique()).issuperset(set(self.revs.nid.unique()))
        )

    def test_nids_nexist(self):
        nexist = AnkiDF()
        with self.assertRaises(ValueError):
            # noinspection PyStatementEffect
            nexist.nid

    def test_cids_revs(self):
        self.assertTrue(
            set(self.revs.cid.unique()).issubset(set(self.cards.cid.unique()))
        )

    def test_cids_notes(self):
        with self.assertRaises(ValueError):
            # noinspection PyStatementEffect
            self.notes.cid

    # --------------------------------------------------------------------------

    def test_mids(self):
        mids2s = {
            "notes": set(self.notes.mid),
            "cards": set(self.cards.mid),
            "revs": set(self.revs.mid),
        }
        mids = set(raw.get_mid2model(self.db).keys())
        for table, mids2 in mids2s.items():
            with self.subTest(table=table):
                self.assertTrue(mids2.issubset(mids))

    def test_dids(self):
        did2s = {"cards": set(self.cards.did), "revs": set(self.revs.did)}
        dids = set(raw.get_did2deck(self.db).keys())
        for table, dids2 in did2s.items():
            with self.subTest(table=table):
                self.assertTrue(dids2.issubset(dids))

    # ==========================================================================

    def test_fields_as_columns(self):
        notes = self.nnotes()
        notes = notes.fields_as_columns()
        cols = our_columns["notes"].copy()
        cols.remove("nflds")
        prefix = notes.fields_as_columns_prefix
        new_cols = [prefix + item for item in ["Front", "Back"]]
        self.assertEqual(sorted(list(notes.columns)), sorted(cols + new_cols))

    def test_fields_as_columns_x2(self):
        notes = self.nnotes()
        notes = notes.fields_as_columns()
        notes2 = notes.fields_as_columns()
        self.assertTrue(notes.equals(notes2))

    def test_fields_as_list(self):
        # Add fields as column, remove original 'flds' column, then
        # add it back from the field columns and see if things still check
        # out
        notes = self.nnotes()
        flds = copy.copy(notes["nflds"].values)
        notes = notes.fields_as_columns().fields_as_list()
        self.assertEqual(list(flds), list(notes["nflds"].values))
        self.assertListEqual(
            sorted(list(notes.columns)), sorted(our_columns["notes"])
        )

    def test_fields_as_list_x2(self):
        notes = self.nnotes()
        notes2 = notes.fields_as_list()
        self.assertTrue(notes.equals(notes2))

    # Convenience
    # ==========================================================================

    def test_list_decks(self):
        decks = self.cards.list_decks()
        self.assertTrue(set(decks).issuperset({"Testing", "EnglishGerman"}))

    def test_list_models(self):
        models = self.notes.list_models()
        self.assertTrue(
            set(models).issuperset({"Basic", "Basic (and reversed card)"})
        )

    # Properties
    # ==========================================================================

    def test_prop_nid(self):
        notes, cards, revs = self.nadfs()
        with self.assertRaises(ValueError):
            notes.nid = ""
        cards.nid = "a"
        revs.nid = "a"
        # noinspection PyUnresolvedReferences
        self.assertEqual(cards.nid.unique().tolist(), ["a"])
        # noinspection PyUnresolvedReferences
        self.assertEqual(revs.nid.unique().tolist(), ["a"])

    def test_prop_cid(self):
        notes, cards, revs = self.nadfs()
        with self.assertRaises(ValueError):
            cards.cid = ""
        with self.assertRaises(ValueError):
            notes.cid = ""
        revs.cid = "a"
        self.assertEqual(revs["cid"].unique().tolist(), ["a"])

    def test_prop_rid(self):
        notes, cards, revs = self.nadfs()
        with self.assertRaises(ValueError):
            revs.rid = ""
        with self.assertRaises(ValueError):
            cards.rid = ""
        with self.assertRaises(ValueError):
            notes.rid = ""

    # Tags
    # ==========================================================================

    def test_list_tags(self):
        tags = self.notes.list_tags()
        self.assertTrue(set(tags).issuperset(["adjective", "noun"]))

    def test_remove_tags(self):
        notes = self.nnotes()
        notes = notes.remove_tag(None)
        self.assertEqual(list(set(map(tuple, notes["ntags"]))), [()])

    def test_add_tags(self):
        notes = self.nnotes().remove_tag(None).add_tag("1145")
        self.assertListEqual(list(set(map(tuple, notes["ntags"]))), [("1145",)])
        notes.add_tag("abc", inplace=True)
        self.assertListEqual(
            list(set(map(tuple, notes["ntags"]))), [("1145", "abc")]
        )
        notes.add_tag(["abc", "def"], inplace=True)
        self.assertListEqual(
            list(set(map(tuple, notes["ntags"]))), [("1145", "abc", "def")]
        )
        notes.add_tag([], inplace=True)
        self.assertListEqual(
            list(set(map(tuple, notes["ntags"]))), [("1145", "abc", "def")]
        )

    def test_has_tag(self):
        notes = self.nnotes().remove_tag(None).add_tag("1145")
        self.assertListEqual(list(notes.has_tag("1145").unique()), [True])
        self.assertListEqual(list(notes.has_tag("asdf").unique()), [False])
        self.assertListEqual(list(notes.has_tag().unique()), [True])
        self.assertListEqual(
            list(notes.has_tag(["asdf", "1145"]).unique()), [True]
        )

    def test_has_tag_natural(self):
        notes = self.notes
        self.assertListEqual(
            sorted(list(notes.has_tag(["some_test_tag"]).unique())),
            [False, True],
        )

    def test_has_tags(self):
        notes = self.nnotes().remove_tag(None).add_tag("1145")
        self.assertListEqual(list(notes.has_tags("1145").unique()), [True])
        self.assertListEqual(list(notes.has_tags("asdf").unique()), [False])
        self.assertListEqual(list(notes.has_tags().unique()), [True])
        self.assertListEqual(
            list(notes.has_tags(["asdf", "1145"]).unique()), [False]
        )
        notes = notes.add_tag("asdf")
        self.assertListEqual(
            list(notes.has_tags(["asdf", "1145"]).unique()), [True]
        )

    def test_remove_tag(self):
        notes = self.nnotes().add_tag(["1145", "asdf"])
        notes.remove_tag("1145", inplace=True)
        self.assertListEqual(list(notes.has_tag(["1145"]).unique()), [False])
        self.assertListEqual(list(notes.has_tag(["asdf"]).unique()), [True])

    # Changes
    # ==========================================================================

    def test_show_modification_unchanged(self):
        for table in ["cards", "revs", "notes"]:
            with self.subTest(table=table):
                adf = self.table2adf[table]
                self.assertEqual(np.sum(~adf.was_modified()), len(adf))
                self.assertEqual(np.sum(~adf.was_added()), len(adf))
                self.assertEqual(len(adf.was_deleted()), 0)
                self.assertEqual(np.sum(~adf.was_modified(adf)), len(adf))
                self.assertEqual(np.sum(~adf.was_added(adf)), len(adf))
                self.assertEqual(len(adf.was_deleted(adf)), 0)

    def test_show_modification_empty(self):
        for table in ["cards", "revs", "notes", "notes_cols"]:
            with self.subTest(table=table):
                if table == "notes_cols":
                    adf = self.ntable("notes")
                else:
                    adf = self.ntable(table)
                adf_old = adf.copy()
                if table == "notes_cols":
                    adf.fields_as_columns(inplace=True)
                adf["new_col"] = "blargh"
                n = len(adf)
                adf = adf.drop(adf.index)
                self.assertEqual(np.sum(~adf.was_modified()), 0)
                self.assertEqual(np.sum(~adf.was_added()), 0)
                self.assertEqual(len(adf.was_deleted()), n)
                self.assertEqual(np.sum(~adf.was_modified(adf_old)), 0)
                self.assertEqual(np.sum(~adf.was_added(adf_old)), 0)
                self.assertEqual(len(adf.was_deleted(adf_old)), n)

    def test_show_modification_all_modified(self):
        for table in ["cards", "revs", "notes", "notes_cols"]:
            with self.subTest(table=table):
                if table == "notes_cols":
                    adf = self.ntable("notes")
                else:
                    adf = self.ntable(table)
                adf_old = adf.copy()
                if table == "notes_cols":
                    adf.fields_as_columns(inplace=True)
                adf[adf.columns[2]] = "changed!"
                self.assertEqual(np.sum(~adf.was_modified()), 0)
                self.assertEqual(np.sum(adf.was_added()), 0)
                self.assertEqual(len(adf.was_deleted()), 0)
                # ----
                self.assertEqual(len(adf.modified_columns(only=True)), len(adf))
                self.assertEqual(
                    len(adf.modified_columns(only=False)), len(adf)
                )
                self.assertEqual(
                    list(adf.modified_columns().loc[adf.index[0]]).index(True),
                    2,
                )
                # ----
                self.assertEqual(np.sum(~adf.was_modified(adf_old)), 0)
                self.assertEqual(np.sum(adf.was_added(adf_old)), 0)
                self.assertEqual(len(adf.was_deleted(adf_old)), 0)
                # ----
                self.assertEqual(
                    len(adf.modified_columns(only=True, other=adf_old)),
                    len(adf),
                )
                self.assertEqual(
                    len(adf.modified_columns(only=False, other=adf_old)),
                    len(adf),
                )
                self.assertEqual(
                    list(
                        adf.modified_columns(other=adf_old).loc[adf.index[0]]
                    ).index(True),
                    2,
                )

    def test_show_modification_some_modified(self):
        for table in ["cards", "revs", "notes", "notes_cols"]:
            with self.subTest(table=table):
                if table == "notes_cols":
                    adf = self.ntable("notes")
                else:
                    adf = self.ntable(table)
                adf_old = adf.copy()
                if table == "notes_cols":
                    adf.fields_as_columns(inplace=True)
                adf.loc[adf.index[0], [adf.columns[2]]] = "changed!"
                self.assertEqual(np.sum(adf.was_modified()), 1)
                self.assertEqual(adf.was_modified().tolist()[0], True)
                self.assertEqual(np.sum(adf.was_added()), 0)
                self.assertEqual(len(adf.was_deleted()), 0)
                # ----
                self.assertEqual(len(adf.modified_columns(only=True)), 1)
                self.assertEqual(
                    len(adf.modified_columns(only=False)), len(adf)
                )
                self.assertEqual(
                    list(adf.modified_columns().loc[adf.index[0]]).index(True),
                    2,
                )
                # ----
                self.assertEqual(np.sum(adf.was_modified(adf_old)), 1)
                self.assertEqual(adf.was_modified(adf_old).tolist()[0], True)
                self.assertEqual(np.sum(adf.was_added(adf_old)), 0)
                self.assertEqual(len(adf.was_deleted(adf_old)), 0)
                # ----
                self.assertEqual(
                    len(adf.modified_columns(only=True, other=adf_old)), 1
                )
                self.assertEqual(
                    len(adf.modified_columns(only=False, other=adf_old)),
                    len(adf),
                )
                self.assertEqual(
                    list(
                        adf.modified_columns(other=adf_old).loc[adf.index[0]]
                    ).index(True),
                    2,
                )

    # Formats
    # ==========================================================================

    def test_reformat_trivial(self):
        for table in ["notes", "revs", "cards"]:
            with self.subTest(table=table):
                adf = self.ntable(table)
                adf2 = adf.normalize()
                self.assertTrue(adf.equals(adf2))

    def test_convert_raw_load_raw(self):
        for table in ["notes", "revs", "cards"]:
            with self.subTest(table=table):
                adf = self.ntable(table).raw()
                df = raw.get_table(self.db, table)
                if table == "notes":
                    df["tags"] = df["tags"].str.strip()
                self.assertTrue(adf.equals(df))

    def test_raw_normalize(self):
        for table in ["notes", "revs", "cards"]:
            with self.subTest(table=table):
                adf = self.ntable(table)
                adf2 = adf.raw().normalize()
                self.assertTrue(adf.equals(adf2))

    # Update modification stamps
    # ==========================================================================

    def test_set_usn(self):
        for table in ["notes", "revs", "cards"]:
            with self.subTest(table=table):
                adf = self.ntable(table)
                print(adf.columns)
                adf[table[0] + "usn"] = 999
                adf_old = adf.copy()
                adf.loc[adf.index[0], adf_old.columns[0]] = "definitely changed"
                adf._set_usn()
                self.assertEqual(
                    adf.loc[
                        adf.index[0], _columns.columns_anki2ours[table]["usn"]
                    ],
                    -1,
                )

    def test_set_mod(self):
        for table in ["notes", "cards"]:
            with self.subTest(table=table):
                adf = self.ntable(table)
                adf_old = adf.copy()
                adf.loc[adf.index[0], adf.columns[0]] = "definitely changed"
                adf._set_mod()
                val1 = adf.loc[
                    adf.index[0], _columns.columns_anki2ours[table]["mod"]
                ]
                val_rest_1 = adf.loc[
                    adf.index[1:], _columns.columns_anki2ours[table]["mod"]
                ]
                val2 = adf_old.loc[
                    adf.index[0], _columns.columns_anki2ours[table]["mod"]
                ]
                val_rest_2 = adf.loc[
                    adf.index[1:], _columns.columns_anki2ours[table]["mod"]
                ]
                self.assertFalse(val1 == val2)
                self.assertListEqual(list(val_rest_1), list(val_rest_2))

    # New
    # ==========================================================================

    # Add cards
    # --------------------------------------------------------------------------

    @staticmethod
    def _cards_dict(card):
        return dict(
            nid=card["nid"],
            cdeck=card["cdeck"],
            cord=card["cord"],
            cmod=card["cmod"],
            cusn=card["cusn"],
            cqueue=card["cqueue"],
            ctype=card["ctype"],
            civl=card["civl"],
            cfactor=card["cfactor"],
            clapses=card["clapses"],
            cleft=card["cleft"],
            cdue=card["cdue"],
        )

    def _test_new_card_default_values(self, cards, **kwargs):
        self.assertEqual(cards["cusn"].unique().tolist(), [-1])
        self.assertEqual(cards["cqueue"].unique().tolist(), ["new"])
        self.assertEqual(cards["ctype"].unique().tolist(), ["learning"])
        self.assertEqual(cards["civl"].unique().tolist(), [0])
        self.assertEqual(cards["cfactor"].unique().tolist(), [0])
        self.assertEqual(cards["creps"].unique().tolist(), [0])
        self.assertEqual(cards["cleft"].unique().tolist(), [0])
        for key, value in kwargs.items():
            self.assertEqual(cards[key].unique().tolist(), [value])

    def test_new_cards_default_values(self):
        empty = self.necards()

        nid1 = 1555579352896
        nid2 = 1557223191575
        nids = [nid1, nid2]
        deck = list(raw.get_did2deck(self.db).values())[0]

        kwargs = dict(cdeck=deck)

        with self.subTest(type="default values single note"):
            self._test_new_card_default_values(
                empty.add_card(nid1, deck), **kwargs
            )
        with self.subTest(type="default values single card"):
            self._test_new_card_default_values(
                empty.add_card(nid1, deck, cord=0), **kwargs, cord=0
            )
        with self.subTest(type="default values several notes"):
            self._test_new_card_default_values(
                empty.add_cards(nids, deck), **kwargs
            )
        with self.subTest(type="default values several notes one cord"):
            self._test_new_card_default_values(
                empty.add_cards(nids, deck, cord=0), **kwargs, cord=0
            )

    def test_new_cards_raises_missing_nid(self):
        empty = self.necards()
        nids = [1555579352896, -15, -16]
        with self.assertRaises(ValueError) as context:
            empty.add_cards(nids, "Default")
        self.assertTrue("-15" in str(context.exception))
        self.assertTrue("-16" in str(context.exception))
        self.assertFalse("1555579352896" in str(context.exception))

    def test_new_cards_raises_inconsistent_model(self):
        empty = self.necards()
        nids = [1555579352896, 1555579337683]
        with self.assertRaises(ValueError) as context:
            empty.add_cards(nids, "Default")
        self.assertTrue("for notes of the same model" in str(context.exception))

    def test_new_cards_raises_missing_deck(self):
        empty = self.necards()
        nids = [1555579352896]
        deck = "not existing for sure"
        with self.assertRaises(ValueError) as context:
            empty.add_cards(nids, deck)
        self.assertTrue(deck in str(context.exception))

    def test_new_cards_raises_due_default_not_new(self):
        empty = self.necards()
        nids = [1555579352896]
        deck = list(raw.get_did2deck(self.db).values())[0]
        with self.assertRaises(ValueError) as context:
            empty.add_cards(nids, deck, cqueue="learning")
        self.assertTrue("Due date can only be set" in str(context.exception))

    def test_new_card_fully_specified(self):
        empty = self.necards()
        empty_combined = self.necards()

        # Careful: Need notes of the same model!
        nid1 = 1555579352896
        nid2 = 1557223191575
        deck1 = list(raw.get_did2deck(self.db).values())[0]
        deck2 = list(raw.get_did2deck(self.db).values())[1]

        init_dict1 = dict(
            nid=nid1,
            cdeck=deck1,
            cord=0,
            cmod=123,
            cusn=5,
            cqueue="learning",
            ctype="relearn",
            civl=5,
            cfactor=17,
            clapses=89,
            cleft=15,
            cdue=178,
        )
        init_dict2 = dict(
            nid=nid2,
            cdeck=deck2,
            cord=0,
            cmod=1123,
            cusn=15,
            cqueue="due",
            ctype="review",
            civl=15,
            cfactor=117,
            clapses=189,
            cleft=115,
            cdue=1178,
        )
        init_dict_combined = dict(
            nid=[nid1, nid2],
            cdeck=[deck1, deck2],
            cord=0,
            cmod=[123, 1123],
            cusn=[5, 15],
            cqueue=["learning", "due"],
            ctype=["relearn", "review"],
            civl=[5, 15],
            cfactor=[17, 117],
            clapses=[89, 189],
            cleft=[15, 115],
            cdue=[178, 1178],
        )

        cid1 = empty.add_card(**init_dict1, inplace=True)[0]
        card1 = empty.loc[cid1]
        cid2 = empty.add_card(**init_dict2, inplace=True)[0]
        card2 = empty.loc[cid2]

        cid1, cid2 = empty_combined.add_cards(
            **init_dict_combined, inplace=True
        )
        card1c = empty_combined.loc[cid1]
        card2c = empty_combined.loc[cid2]

        self.assertDictEqual(init_dict1, self._cards_dict(card1))
        self.assertDictEqual(init_dict2, self._cards_dict(card2))
        self.assertDictEqual(init_dict1, self._cards_dict(card1c))
        self.assertDictEqual(init_dict2, self._cards_dict(card2c))

        self.assertEqual(len(empty), 2)
        self.assertEqual(len(empty_combined), 2)

    def test_new_cards_vs_new_card(self):
        # Also done in test_new_card_fully_specified

        empty = self.necards()
        empty2 = self.necards()

        nid = list(raw.get_nid2mid(self.db).keys())[0]
        deck = list(raw.get_did2deck(self.db).values())[0]

        init_dict2 = dict(
            nid=[nid],
            cdeck=deck,
            cord=0,
            cmod=123,
            cusn=5,
            cqueue="learning",
            ctype="relearn",
            civl=5,
            cfactor=17,
            clapses=89,
            cleft=15,
            cdue=178,
        )
        init_dict1 = copy.deepcopy(init_dict2)
        init_dict1["nid"] = nid

        cids = empty2.add_cards(**init_dict2, inplace=True)
        card2 = empty2.loc[cids[0]]

        cid = empty.add_card(**init_dict1, inplace=True)[0]
        card1 = empty.loc[cid]

        self.assertDictEqual(self._cards_dict(card2), self._cards_dict(card1))

    # Add notes
    # --------------------------------------------------------------------------

    def test_new_notes_raises_inconsistent(self):
        with self.assertRaises(ValueError):
            self.nnotes().add_notes("Basic", [["1", "2"]], ntags=[["1"], ["2"]])
        with self.assertRaises(ValueError):
            self.nnotes().add_notes("Basic", [["1", "2"]], nid=[123, 124])
        with self.assertRaises(ValueError):
            self.nnotes().add_notes("Basic", [["1", "2"]], nguid=[123, 124])

    def test_new_notes_raises_nid_clash(self):
        with self.assertRaises(ValueError):
            self.nnotes().add_note("Basic", ["11", "12"], nid=10).add_note(
                "Basic", ["21", "22"], nid=10
            )
        with self.assertRaises(ValueError):
            self.nnotes().add_notes(
                "Basic", [["11", "12"], ["22", "22"]], nid=[10, 10]
            )

    def test_new_notes_raises_nguid_clash(self):
        with self.assertRaises(ValueError):
            self.nnotes().add_notes(
                "Basic", [["11", "12"], ["21", "22"]], nguid=[10, 10]
            )
        with self.assertRaises(ValueError):
            self.nnotes().add_note("Basic", ["11", "12"], nguid=10).add_note(
                "Basic", ["21", "22"], nguid=10
            )

    def test_new_notes_fields_as_columns(self):
        empty = self.nenotes()
        empty.add_notes(
            "Basic",
            [["field1", "field2"], ["field21", "field22"]],
            ntags=[["tag1", "tag2"], ["tag21", "tag22"]],
            nguid=["cryptic", "cryptic2"],
            nmod=[124, 1235],
            nusn=[42, 17],
            nid=[123, 125],
            inplace=True,
        )

        empty2 = self.nenotes().fields_as_columns()
        empty2.add_notes(
            "Basic",
            [["field1", "field2"], ["field21", "field22"]],
            ntags=[["tag1", "tag2"], ["tag21", "tag22"]],
            nguid=["cryptic", "cryptic2"],
            nmod=[124, 1235],
            nusn=[42, 17],
            nid=[123, 125],
            inplace=True,
        )

        self.assertDictEqual(
            empty.fields_as_columns().to_dict(), empty2.to_dict()
        )

    @staticmethod
    def _notes_dict(notes):
        return {
            "nmodel": notes["nmodel"],
            "nflds": notes["nflds"],
            "ntags": notes["ntags"],
            "nguid": notes["nguid"],
            "nmod": notes["nmod"],
            "nusn": notes["nusn"],
        }

    def test_new_note_empty_fully_specified(self):
        empty = self.nenotes()

        init_dict = dict(
            nmodel="Basic",
            nflds=["field1", "field2"],
            ntags=["tag1", "tag2"],
            nguid="cryptic",
            nmod=124,
            nusn=42,
        )
        nid = empty.add_note(nid=123, **init_dict, inplace=True)
        self.assertEqual(nid, 123)
        note = empty.loc[nid]
        self.assertDictEqual(init_dict, self._notes_dict(note))
        self.assertEqual(len(empty), 1)

        init_dict2 = dict(
            nmodel="Basic",
            nflds=["field21", "field22"],
            ntags=["tag21", "tag22"],
            nguid="cryptic2",
            nmod=1235,
            nusn=17,
        )
        nid = empty.add_note(nid=125, **init_dict2, inplace=True)
        self.assertEqual(nid, 125)
        note = empty.loc[125]
        self.assertDictEqual(init_dict2, self._notes_dict(note))
        self.assertEqual(len(empty), 2)

        empty2 = self.nenotes()
        empty2.add_notes(
            "Basic",
            [["field1", "field2"], ["field21", "field22"]],
            ntags=[["tag1", "tag2"], ["tag21", "tag22"]],
            nguid=["cryptic", "cryptic2"],
            nmod=[124, 1235],
            nusn=[42, 17],
            nid=[123, 125],
            inplace=True,
        )
        self.assertTrue(empty.equals(empty2))

    def test_new_note_raises_suplicate(self):
        empty = self.nenotes()
        empty.add_note("Basic", ["f1", "f2"], nid=10, inplace=True)
        self.assertEqual(len(empty), 1)
        with self.assertRaises(ValueError):
            empty.add_note("Basic", ["f3", "f4"], nid=10, inplace=True)

    def test_new_note_default_values(self):
        empty = self.nenotes()

        init_dict = dict(nmodel="Basic", nflds=["field1", "field2"])
        nid = empty.add_note(nid=123, **init_dict, inplace=True)
        self.assertEqual(nid, 123)
        note = empty.loc[nid].to_dict()
        self.assertEqual(note["nmodel"], init_dict["nmodel"])
        self.assertEqual(note["nflds"], init_dict["nflds"])

    def test_new_note_raises(self):
        empty = self.nenotes()
        with self.assertRaises(ValueError):
            empty.add_note("doesntexist", [])
        with self.assertRaises(ValueError):
            empty.add_note("Basic", ["1", "2", "3"])

    def test_new_notes_equivalent_field_specifications(self):
        empty1 = self.nenotes()
        empty2 = self.nenotes()
        empty3 = self.nenotes()

        empty1.add_notes("Basic", [["11", "12"], ["21", "22"]], inplace=True)
        empty2.add_notes(
            "Basic",
            [{"Front": "11", "Back": "12"}, {"Front": "21", "Back": "22"}],
            inplace=True,
        )
        empty3.add_notes(
            "Basic", {"Front": ["11", "21"], "Back": ["12", "22"]}, inplace=True
        )
        self.assertListEqual(empty1["nflds"].tolist(), empty2["nflds"].tolist())
        self.assertListEqual(empty2["nflds"].tolist(), empty3["nflds"].tolist())

    def test_new_notes_equivalent_field_specifications_fields_as_columns(self):
        empty1 = self.nenotes().fields_as_columns()
        empty2 = self.nenotes().fields_as_columns()
        empty3 = self.nenotes().fields_as_columns()

        empty1.add_notes("Basic", [["11", "12"], ["21", "22"]], inplace=True)
        empty2.add_notes(
            "Basic",
            [{"Front": "11", "Back": "12"}, {"Front": "21", "Back": "22"}],
            inplace=True,
        )
        empty3.add_notes(
            "Basic", {"Front": ["11", "21"], "Back": ["12", "22"]}, inplace=True
        )

        p = empty1.fields_as_columns_prefix

        self.assertListEqual(
            empty1[p + "Front"].tolist(), empty2[p + "Front"].tolist()
        )
        self.assertListEqual(
            empty2[p + "Front"].tolist(), empty3[p + "Front"].tolist()
        )
        self.assertListEqual(
            empty1[p + "Back"].tolist(), empty2[p + "Back"].tolist()
        )
        self.assertListEqual(
            empty2[p + "Back"].tolist(), empty3[p + "Back"].tolist()
        )

    # Help
    # ==========================================================================

    def test_help_col(self):
        for table, adf in self.table2adf.items():
            with self.subTest(table=table):
                cols = list(adf.columns) + [adf.index.name]
                for col in cols:
                    self.assertIsInstance(adf.help_col(col, ret=True), str)

    def test_help_cols_auto(self):
        for table, adf in self.table2adf.items():
            with self.subTest(table=table):
                df = adf.help_cols()
                self.assertListEqual(
                    list(df.columns),
                    ["AnkiColumn", "Table", "Description", "Native", "Default"],
                )
                self.assertListEqual(
                    sorted(adf.columns),
                    sorted(list(set(df.index))),  # nid, cid appear twice
                )

    def test_help(self):
        notes = self.notes
        hlp = notes.help(ret=True)
        self.assertTrue(isinstance(hlp, str))


class TestAnkiDFv1(TestAnkiDF):
    db_path = (
        pathlib.Path(__file__).parent
        / "data"
        / "few_basic_cards"
        / "collection_v1.anki2"
    )


if __name__ == "__main__":
    unittest.main()
