#!/usr/bin/env python3

# std
import unittest
import pathlib
import copy

# ours
from ankipandas.core_functions import *
# for hidden
import ankipandas.core_functions as core_functions
from ankipandas.test.shared import revlog_cols, note_cols, card_cols


class TestCoreFunctions(unittest.TestCase):
    def setUp(self):
        self.db = load_db(
            pathlib.Path(__file__).parent / "data" / "few_basic_cards" /
            "collection.anki2"
        )

    def tearDown(self):
        close_db(self.db)

    def test_get_cards(self):
        cards = get_cards(self.db)
        self.assertEqual(len(cards), 3)
        self.assertEqual(
            list(sorted(cards.columns)),
            sorted(card_cols)
        )

    def test_get_notes(self):
        notes = get_notes(self.db)
        self.assertEqual(len(notes), 2)
        self.assertEqual(
            list(sorted(notes.columns)),
            sorted(note_cols)
        )

    def test_get_revlog(self):
        revlog = get_revlog(self.db)
        # todo assert length
        self.assertEqual(
            list(sorted(revlog.columns)),
            sorted(revlog_cols)
        )

    def test_get_deck_info(self):
        get_deck_info(self.db)
        # todo

    def test_get_deck_names(self):
        names = get_deck_names(self.db)
        self.assertDictEqual(
            names,
            {"1": "Default"}
        )

    def test_get_model_info(self):
        get_model_info(self.db)
        # todo

    def test_get_model_names(self):
        names = get_model_names(self.db)
        self.assertIn("Basic", names.values())
        self.assertIn("Cloze", names.values())
        self.assertEqual(len(names), 5)

    def test_get_field_names(self):
        fnames = get_field_names(self.db)
        mnames = get_model_names(self.db)
        fnames = {
            mnames[mid]: fnames[mid]
            for mid in mnames
        }
        self.assertEqual(len(fnames), len(get_model_names(self.db)))
        self.assertListEqual(
            fnames["Basic"], ["Front", "Back"]
        )

    def test_merge_note_info(self):
        cards = get_cards(self.db)
        merged = merge_note_info(self.db, cards)
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(list(
                set(card_cols) | set(note_cols) |
                {"ndata", "nflags", "nmod", "nusn"}  # clashes
            ))
        )

    def test_merge_card_info(self):
        revlog = get_revlog(self.db)
        merged = merge_card_info(self.db, revlog)
        self.assertListEqual(
            sorted(list(merged.columns)),
            sorted(list(
                set(revlog_cols) | set(card_cols) |
                {"civl", "ctype", "cusn", "cid", "cfactor"}  # clashes
            ))
        )

    def test_add_nids(self):
        cards = get_cards(self.db)
        cards = add_nids(self.db, cards)
        self.assertIn("nid", list(cards.columns))
        self.assertListEqual(
            sorted(list(cards["nid"].unique())),
            sorted(list(get_notes(self.db)["id"].unique()))
        )

    def test_add_mids(self):
        notes = get_notes(self.db)
        notes = add_mids(self.db, notes)
        self.assertEqual(
            len(notes["mid"].unique()),
            2  # we don't have notesfor every model
        )

    def test_add_model_names(self):
        notes = get_notes(self.db)
        notes = add_mids(self.db, notes)
        notes = add_model_names(self.db, notes)
        self.assertEqual(
            sorted(list(notes["mname"].unique())),
            ["Basic", 'Basic (and reversed card)']
        )

    def test_add_deck_names(self):
        cards = get_cards(self.db)
        cards = add_deck_names(self.db, cards)
        self.assertEqual(
            sorted(list(cards["dname"].unique())),
            ["Default"]
        )

    def test_add_fields_as_columns(self):
        notes = get_notes(self.db)
        notes = add_fields_as_columns(self.db, notes)
        notes = add_model_names(self.db, notes)
        self.assertEqual(
            sorted(list(notes.columns)),
            sorted(note_cols + ["mname", "Front", "Back"])
        )
        self.assertEqual(
            list(notes.query("mname=='Basic'")["Front"].unique()),
            ["Basic: Front"]
        )


class TestUtils(unittest.TestCase):
    def test__replace_df_inplace(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df_new = pd.DataFrame({"a": [1]})
        core_functions._replace_df_inplace(df, df_new)
        self.assertEqual(len(df), 1)
        self.assertEqual(len(df.columns), 1)
        self.assertListEqual(list(df["a"].values), [1])


class TestMergeDfs(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            "id_df": [1, 2, 3, 1, 1],
            "clash": ["a", "b", "c", "a", "a"]
        })
        self.df_add = pd.DataFrame({
            "id_add": [1, 2, 3],
            "value": [4, 5, 6],
            "drop": [7, 8, 9],
            "ignore": [10, 11, 12],
            "clash": [1, 1, 1]
        })

    def test_merge_dfs(self):
        df_merged = merge_dfs(
            self.df,
            self.df_add,
            id_df="id_df",
            id_add="id_add",
            prepend="_",
            columns=["value", "drop", "clash"],
            drop_columns=["id_add", "drop"]
        )
        self.assertListEqual(
            sorted(list(df_merged.columns)),
            ["_clash", "clash", "id_df", "value"]
        )
        self.assertListEqual(sorted(list(df_merged["value"])), [4, 4, 4, 5, 6])

    def test_merge_dfs_prepend_all(self):
        df_merged = merge_dfs(
            self.df,
            self.df_add,
            id_df="id_df",
            id_add="id_add",
            prepend="_",
            prepend_clash_only=False
        )
        self.assertListEqual(
            sorted(list(df_merged.columns)),
            ['_clash', '_drop', '_id_add', '_ignore', '_value', 'clash',
             'id_df']
        )

    def test_merge_dfs_inplace(self):
        df = copy.deepcopy(self.df)
        merge_dfs(
            df,
            self.df_add,
            id_df="id_df",
            id_add="id_add",
            inplace=True
        )
        self.assertListEqual(
            sorted(list(df.columns)),
            ['clash_x', 'clash_y', 'drop', 'id_add', 'id_df', 'ignore', 'value']
        )
        self.assertListEqual(sorted(list(df["value"])), [4, 4, 4, 5, 6])


if __name__ == "__main__":
    unittest.main()