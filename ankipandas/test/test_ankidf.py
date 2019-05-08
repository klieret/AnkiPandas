#!/usr/bin/env python3

""" Most of the functionality of the AnkiDataFrames is already tested in
test_core, because that saves to write a lot of duplicate code.

Everything else is tested here.
"""

# std
import pathlib
import unittest
import copy
import shutil
import tempfile

# 3rd
import numpy as np

# ours
from ankipandas.ankidf import AnkiDataFrame as AnkiDF
from ankipandas._columns import our_columns
import ankipandas.raw as raw
import ankipandas._columns as _columns


class TestAnkiDF(unittest.TestCase):
    def setUp(self):
        self.db_path = pathlib.Path(__file__).parent / "data" / \
                       "few_basic_cards" / "collection.anki2"
        self.db = raw.load_db(self.db_path)

        # Do not modify this one!
        self.notes = AnkiDF.notes(self.db_path)
        self.cards = AnkiDF.cards(self.db_path)
        self.revs = AnkiDF.revs(self.db_path)
        self.table2adf = {
            "notes": self.notes,
            "cards": self.cards,
            "revs": self.revs
        }
        self.adfs = [self.notes, self.cards, self.revs]

    def nnotes(self):
        return self.notes.copy()

    def ncards(self):
        return self.cards.copy()

    def nrevs(self):
        return self.revs.copy()

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
            "revs": self.nrevs()
        }

    def nadfs(self):
        return [self.nnotes(), self.ncards(), self.nrevs()]

    # Test constructors
    # ==========================================================================

    def test_empty(self):
        eadfs = {
            "notes": AnkiDF.notes(self.db_path, empty=True),
            "cards": AnkiDF.cards(self.db_path, empty=True),
            "revs": AnkiDF.revs(self.db_path, empty=True)
        }
        for table, eadf in eadfs.items():
            self.assertEqual(len(eadf), 0)
            adf = self.table2adf[table]
            self.assertListEqual(
                sorted(list(adf.columns)),
                sorted(list(eadf.columns))
            )

    def test_tags(self):
        self.assertListEqual(
            list(self.notes.query("index=='1555579337683'")["ntags"].values)[0],
            ['other_test_tag']
        )
        self.assertListEqual(
            list(self.notes.query("index=='1555579352896'")["ntags"].values)[0],
            ['some_test_tag']
        )

    # Test merging
    # ==========================================================================

    def test_merge_notes_cards(self):
        merged = self.ncards().merge_notes()
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(list(
                set(our_columns["cards"]) | set(our_columns["notes"])
            ))
        )

    def test_merge_notes_revs(self):
        merged = self.nrevs().merge_notes()
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(list(
                # Note: 'nid' is not a notes column.
                set(our_columns["revs"]) | set(our_columns["notes"]) | {"nid"}
            ))
        )

    def test_merge_notes_raises(self):
        with self.assertRaises(ValueError):
            self.nnotes().merge_notes()

    def test_merge_cards(self):
        merged = self.nrevs().merge_cards()
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(list(
                set(our_columns["revs"]) | set(our_columns["cards"])
            ))
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
        self.assertListEqual(
            list(self.notes.index),
            list(self.notes.nid)
        )
        self.assertListEqual(
            list(self.notes.index),
            list(raw.get_table(self.db, "notes")["id"].unique())
        )
        self.assertEqual(
            len(self.notes.nid.unique()),
            len(self.notes.nid)
        )

    def test_cids_cards(self):
        self.assertListEqual(
            list(self.cards.index),
            list(self.cards.cid)
        )
        self.assertListEqual(
            list(self.cards.index),
            list(raw.get_table(self.db, "cards")["id"].unique())
        )
        self.assertEqual(
            len(self.cards.cid.unique()),
            len(self.cards.cid)
        )

    def test_rids_revs(self):
        self.assertListEqual(
            list(self.revs.index),
            list(self.revs.rid)
        )
        self.assertListEqual(
            list(self.revs.index),
            list(raw.get_table(self.db, "revs")["id"].unique())
        )
        self.assertEqual(
            len(self.revs.rid.unique()),
            len(self.revs.rid)
        )

    # Slightly more elaborate cases
    # --------------------------------------------------------------------------

    def test_nids_cards(self):
        self.assertListEqual(
            sorted(list(self.cards.nid.unique())),
            sorted(list(self.notes.nid.unique()))
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
            "revs": set(self.revs.mid)
        }
        mids = set(raw.get_mid2model(self.db).keys())
        for table, mids2 in mids2s.items():
            with self.subTest(table=table):
                self.assertTrue(mids2.issubset(mids))

    def test_dids(self):
        did2s = {
            "cards": set(self.cards.did),
            "revs": set(self.revs.did)
        }
        print(did2s)
        dids = set(raw.get_did2deck(self.db).keys())
        print(dids)
        for table, dids2 in did2s.items():
            with self.subTest(table=table):
                self.assertTrue(dids2.issubset(dids))

    # ==========================================================================

    def test_fields_as_columns(self):
        notes = self.nnotes().fields_as_columns()
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
        notes = self.nnotes()
        flds = copy.copy(notes["nflds"].values)
        notes = notes.fields_as_columns().fields_as_list()
        self.assertEqual(
            list(flds),
            list(notes["nflds"].values)
        )
        self.assertListEqual(
            sorted(list(notes.columns)),
            sorted(our_columns["notes"])
        )

    # Convenience
    # ==========================================================================

    def test_list_decks(self):
        decks = self.notes.list_decks()
        self.assertTrue(
            set(decks).issuperset({"Testing", "EnglishGerman"})
        )

    def test_list_models(self):
        models = self.notes.list_models()
        self.assertTrue(
            set(models).issuperset({
                "Basic",
                'Basic (and reversed card)',
                'Basic (optional reversed card)',
                'Basic (type in the answer)',
                'Cloze'
            })
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
        self.assertTrue(
            set(tags).issuperset(["adjective", "noun"])
        )

    def test_remove_tags(self):
        notes = self.nnotes()
        notes = notes.remove_tag(None)
        self.assertEqual(
            list(set(map(tuple, notes["ntags"]))),
            [()]
        )

    def test_add_tags(self):
        notes = self.nnotes().remove_tag(None).add_tag("1145")
        self.assertListEqual(
            list(set(map(tuple, notes["ntags"]))),
            [('1145', )]
        )
        notes.add_tag("abc", inplace=True)
        self.assertListEqual(
            list(set(map(tuple, notes["ntags"]))),
            [('1145', "abc")]
        )
        notes.add_tag(["abc", "def"], inplace=True)
        self.assertListEqual(
            list(set(map(tuple, notes["ntags"]))),
            [('1145', "abc", "def")]
        )
        notes.add_tag([], inplace=True)
        self.assertListEqual(
            list(set(map(tuple, notes["ntags"]))),
            [('1145', "abc", "def")]
        )

    def test_has_tag(self):
        notes = self.nnotes().remove_tag(None).add_tag("1145")
        self.assertListEqual(
            list(notes.has_tag("1145").unique()),
            [True]
        )
        self.assertListEqual(
            list(notes.has_tag("asdf").unique()),
            [False]
        )
        self.assertListEqual(
            list(notes.has_tag().unique()),
            [True]
        )
        self.assertListEqual(
            list(notes.has_tag(["asdf", "1145"]).unique()),
            [True]
        )

    def test_has_tag_natural(self):
        notes = self.notes
        self.assertListEqual(
            sorted(list(notes.has_tag(["some_test_tag"]).unique())),
            [False, True]
        )

    def test_has_tags(self):
        notes = self.nnotes().remove_tag(None).add_tag("1145")
        self.assertListEqual(
            list(notes.has_tags("1145").unique()),
            [True]
        )
        self.assertListEqual(
            list(notes.has_tags("asdf").unique()),
            [False]
        )
        self.assertListEqual(
            list(notes.has_tags().unique()),
            [True]
        )
        self.assertListEqual(
            list(notes.has_tags(["asdf", "1145"]).unique()),
            [False]
        )
        notes = notes.add_tag("asdf")
        self.assertListEqual(
            list(notes.has_tags(["asdf", "1145"]).unique()),
            [True]
        )

    def test_remove_tag(self):
        notes = self.nnotes().add_tag(["1145", "asdf"])
        notes.remove_tag("1145", inplace=True)
        self.assertListEqual(
            list(notes.has_tag(["1145"]).unique()),
            [False]
        )
        self.assertListEqual(
            list(notes.has_tag(["asdf"]).unique()),
            [True]
        )

    # Changes
    # ==========================================================================

    def test_show_modification_unchanged(self):
        for table in ["cards", "revs", "notes"]:
            with self.subTest(table=table):
                adf = self.table2adf[table]
                self.assertEqual(
                    np.sum(~adf.was_modified()),
                    len(adf)
                )
                self.assertEqual(
                    np.sum(~adf.was_added()),
                    len(adf)
                )
                self.assertEqual(
                    len(adf.was_deleted()),
                    0
                )
                self.assertEqual(
                    np.sum(~adf.was_modified(adf)),
                    len(adf)
                )
                self.assertEqual(
                    np.sum(~adf.was_added(adf)),
                    len(adf)
                )
                self.assertEqual(
                    len(adf.was_deleted(adf)),
                    0
                )

    def test_show_modification_empty(self):
        for table in ["cards", "revs", "notes"]:
            with self.subTest(table=table):
                adf = self.ntable(table)
                adf_old = adf.copy()
                n = len(adf)
                adf = adf.drop(adf.index)
                self.assertEqual(
                    np.sum(~adf.was_modified()),
                    0
                )
                self.assertEqual(
                    np.sum(~adf.was_added()),
                    0
                )
                self.assertEqual(
                    len(adf.was_deleted()),
                    n
                )
                self.assertEqual(
                    np.sum(~adf.was_modified(adf_old)),
                    0
                )
                self.assertEqual(
                    np.sum(~adf.was_added(adf_old)),
                    0
                )
                self.assertEqual(
                    len(adf.was_deleted(adf_old)),
                    n
                )

    def test_show_modification_all_modified(self):
        for table in ["cards", "revs", "notes"]:
            with self.subTest(table=table):
                adf = self.ntable(table)
                adf_old = adf.copy()
                adf[adf.columns[2]] = "changed!"
                self.assertEqual(
                    np.sum(~adf.was_modified()),
                    0
                )
                self.assertEqual(
                    np.sum(adf.was_added()),
                    0
                )
                self.assertEqual(
                    len(adf.was_deleted()),
                    0
                )
                # ----
                self.assertEqual(
                    len(adf.modified_columns(only=True)),
                    len(adf)
                )
                self.assertEqual(
                    len(adf.modified_columns(only=False)),
                    len(adf)
                )
                self.assertEqual(
                    list(adf.modified_columns().loc[adf.index[0]]).index(True),
                    2
                )
                # ----
                self.assertEqual(
                    np.sum(~adf.was_modified(adf_old)),
                    0
                )
                self.assertEqual(
                    np.sum(adf.was_added(adf_old)),
                    0
                )
                self.assertEqual(
                    len(adf.was_deleted(adf_old)),
                    0
                )
                # ----
                self.assertEqual(
                    len(adf.modified_columns(only=True, other=adf_old)),
                    len(adf)
                )
                self.assertEqual(
                    len(adf.modified_columns(only=False, other=adf_old)),
                    len(adf)
                )
                self.assertEqual(
                    list(
                        adf.modified_columns(other=adf_old).loc[adf.index[0]]
                    ).index(True),
                    2
                )

    def test_show_modification_some_modified(self):
        for table in ["cards", "revs", "notes"]:
            with self.subTest(table=table):
                adf = self.ntable(table)
                adf_old = adf.copy()
                adf.loc[adf.index[0], [adf.columns[2]]] = "changed!"
                self.assertEqual(
                    np.sum(adf.was_modified()),
                    1
                )
                self.assertEqual(
                    adf.was_modified().tolist()[0],
                    True
                )
                self.assertEqual(
                    np.sum(adf.was_added()),
                    0
                )
                self.assertEqual(
                    len(adf.was_deleted()),
                    0
                )
                # ----
                self.assertEqual(
                    len(adf.modified_columns(only=True)),
                    1
                )
                self.assertEqual(
                    len(adf.modified_columns(only=False)),
                    len(adf)
                )
                self.assertEqual(
                    list(adf.modified_columns().loc[adf.index[0]]).index(True),
                    2
                )
                # ----
                self.assertEqual(
                    np.sum(adf.was_modified(adf_old)),
                    1
                )
                self.assertEqual(
                    adf.was_modified(adf_old).tolist()[0],
                    True
                )
                self.assertEqual(
                    np.sum(adf.was_added(adf_old)),
                    0
                )
                self.assertEqual(
                    len(adf.was_deleted(adf_old)),
                    0
                )
                # ----
                self.assertEqual(
                    len(adf.modified_columns(only=True, other=adf_old)),
                    1
                )
                self.assertEqual(
                    len(adf.modified_columns(only=False, other=adf_old)),
                    len(adf)
                )
                self.assertEqual(
                    list(
                        adf.modified_columns(other=adf_old).loc[adf.index[0]]
                    ).index(True),
                    2
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
                adf_old = adf.copy()
                adf.loc[adf.index[0], adf_old.columns[0]] = "definitely changed"
                adf._set_usn()
                # fixme: this is probably already true before
                self.assertEqual(
                    adf.loc[
                        adf.index[0],
                        _columns.columns_anki2ours[table]["usn"]
                    ],
                    -1
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
                self.assertListEqual(
                    list(val_rest_1),
                    list(val_rest_2)
                )

    # Write
    # ==========================================================================

    def test_read_write_identical(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = shutil.copy2(str(self.db_path), tmpdir)
            (pathlib.Path(tmpdir) / "backups").mkdir()
            for table in self.table2adf:
                with self.subTest(table=table):
                    adf = AnkiDF._table_constructor(
                        path=db_path, user=None, table=table
                    )
                    adf.write("update")
                    adf2 = AnkiDF._table_constructor(
                        path=db_path, user=None, table=table
                    )
                    adf_old = AnkiDF._table_constructor(
                        path=self.db_path, user=None, table=table
                    )
                    self.assertTrue(adf2.equals(adf_old))

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
                    ["AnkiColumn", "Table", "Description", "Native", "Default"]
                )
                self.assertListEqual(
                    sorted(adf.columns),
                    sorted(list(set(df.index)))  # nid, cid appear twice
                )

    def test_help(self):
        notes = self.notes
        hlp = notes.help(ret=True)
        self.assertTrue(isinstance(hlp, str))


if __name__ == "__main__":
    unittest.main()
