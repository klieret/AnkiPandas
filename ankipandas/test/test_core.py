#!/usr/bin/env python3

# std
import unittest
import shutil
import tempfile

# ours
from ankipandas.core_functions import *
from ankipandas.ankidf import AnkiDataFrame as AnkiDF
from ankipandas.columns import our_columns


class TestCoreFunctionsRead(unittest.TestCase):
    def setUp(self):
        self.db_path = pathlib.Path(__file__).parent / "data" / \
                       "few_basic_cards" / "collection.anki2"
        self.db = load_db(self.db_path)

    def tearDown(self):
        close_db(self.db)

    def test_cards(self):
        cards = AnkiDF.cards(self.db_path)
        self.assertEqual(len(cards), 3)
        self.assertEqual(
            list(sorted(cards.columns)),
            sorted(our_columns["cards"])
        )

    def test_notes(self):
        notes = AnkiDF.notes(self.db_path)
        self.assertEqual(len(notes), 2)
        self.assertEqual(
            list(sorted(notes.columns)),
            sorted(our_columns["notes"])
        )

    def test_get_revs(self):
        revs = AnkiDF.revs(self.db_path)
        # todo assert length
        self.assertEqual(
            list(sorted(revs.columns)),
            sorted(our_columns["revs"])
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
        models = get_model_names(self.db)
        fnames = {
            models[mid]: fnames[mid]
            for mid in models
        }
        self.assertEqual(len(fnames), len(get_model_names(self.db)))
        self.assertListEqual(
            fnames["Basic"], ["Front", "Back"]
        )


class TestCoreWrite(unittest.TestCase):
    def setUp(self):
        self.db_read_path = pathlib.Path(__file__).parent / "data" \
            / "few_basic_cards" / "collection.anki2"
        self.db_read = load_db(self.db_read_path)
        self.db_write_dir = tempfile.TemporaryDirectory()
        self.db_write_path = \
            pathlib.Path(self.db_write_dir.name) / "collection.anki2"
        self._reset()

    def _reset(self):
        shutil.copy(str(self.db_read_path), str(self.db_write_path))
        self.db_write = load_db(self.db_write_path)

    def tearDown(self):
        self.db_read.close()
        self.db_write.close()
        self.db_write_dir.cleanup()

    def _check_db_equal(self):
        notes = get_table(self.db_read, "notes")
        cards = get_table(self.db_read, "cards")
        revlog = get_table(self.db_read, "revs")
        notes2 = get_table(self.db_write, "notes")
        cards2 = get_table(self.db_write, "cards")
        revlog2 = get_table(self.db_write, "revs")
        self.assertListEqual(
            list(notes.values.tolist()), list(notes2.values.tolist())
        )
        self.assertListEqual(
            list(cards.values.tolist()), list(cards2.values.tolist())
        )
        self.assertListEqual(
            list(revlog.values.tolist()), list(revlog2.values.tolist())
        )

    def test_rw_identical(self):
        notes = get_table(self.db_read, "notes")
        cards = get_table(self.db_read, "cards")
        revlog = get_table(self.db_read, "revs")
        for mode in ["update", "replace", "append"]:
            with self.subTest(mode=mode):
                self._reset()
                set_notes(self.db_write, notes, mode)
                set_cards(self.db_write, cards, mode)
                set_revs(self.db_write, revlog, mode)
                self._check_db_equal()

    def test_update(self):
        notes2 = get_table(self.db_read, "notes")
        notes = get_table(self.db_read, "notes")
        for mode in ["update", "replace", "append"]:
            with self.subTest(mode=mode):
                self._reset()
                notes2.loc[notes2["id"] == 1555579337683, "tags"] = "mytesttag"
                set_notes(self.db_write, notes2, mode)
                if mode == "append":
                    self._check_db_equal()
                else:
                    notes2 = get_table(self.db_write, "notes")
                    chtag = notes2.loc[notes2["id"] == 1555579337683, "tags"]
                    self.assertListEqual(
                        list(chtag.values.tolist()),
                        ["mytesttag"]
                    )
                    unchanged = notes.loc[notes["id"] != 1555579337683, :]
                    unchanged2 = notes2.loc[notes2["id"] != 1555579337683, :]

                    self.assertListEqual(
                        list(unchanged.values.tolist()),
                        list(unchanged2.values.tolist())
                    )


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
            ['_clash', '_drop', '_ignore', '_value', 'clash',
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
            ['clash_x', 'clash_y', 'drop', 'id_df', 'ignore', 'value']
        )
        self.assertListEqual(sorted(list(df["value"])), [4, 4, 4, 5, 6])


if __name__ == "__main__":
    unittest.main()
