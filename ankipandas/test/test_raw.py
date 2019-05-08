#!/usr/bin/env python3

# std
import copy
import unittest
import shutil
import tempfile

# ours
from ankipandas.raw import *
from ankipandas.ankidf import AnkiDataFrame as AnkiDF
from ankipandas._columns import our_columns
from ankipandas.util.dataframe import merge_dfs


class TestRawRead(unittest.TestCase):
    def setUp(self):
        self.db_path = pathlib.Path(__file__).parent / "data" / \
                       "few_basic_cards" / "collection.anki2"
        self.db = load_db(self.db_path)

    def tearDown(self):
        close_db(self.db)

    def test_cards(self):
        cards = AnkiDF.cards(self.db_path)
        self.assertGreater(len(cards), 11)
        self.assertEqual(
            list(sorted(cards.columns)),
            sorted(our_columns["cards"])
        )

    def test_notes(self):
        notes = AnkiDF.notes(self.db_path)
        self.assertGreater(len(notes), 6)
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
        names = get_did2deck(self.db)
        self.assertTrue(
            set(names.values()).issuperset({"Testing", "EnglishGerman"})
        )

    def test_get_model_info(self):
        get_model_info(self.db)
        # todo

    def test_get_model_names(self):
        names = get_mid2model(self.db)
        self.assertIn("Basic", names.values())
        self.assertIn("Cloze", names.values())
        self.assertEqual(len(names), 5)

    def test_get_field_names(self):
        fnames = get_mid2fields(self.db)
        models = get_mid2model(self.db)
        fnames = {
            models[mid]: fnames[mid]
            for mid in models
        }
        self.assertEqual(len(fnames), len(get_mid2model(self.db)))
        self.assertListEqual(
            fnames["Basic"], ["Front", "Back"]
        )


class TestRawWrite(unittest.TestCase):
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
        # noinspection PyUnresolvedReferences
        self.assertListEqual(
            notes.values.tolist(), notes2.values.tolist()
        )
        # noinspection PyUnresolvedReferences
        self.assertListEqual(
            cards.values.tolist(), cards2.values.tolist()
        )
        # noinspection PyUnresolvedReferences
        self.assertListEqual(
            revlog.values.tolist(), revlog2.values.tolist()
        )

    def test_rw_identical(self):
        notes = get_table(self.db_read, "notes")
        cards = get_table(self.db_read, "cards")
        revlog = get_table(self.db_read, "revs")
        for mode in ["update", "replace", "append"]:
            with self.subTest(mode=mode):
                self._reset()
                set_table(self.db_write, notes, "notes", mode)
                set_table(self.db_write, cards, "cards", mode)
                set_table(self.db_write, revlog, "revs", mode)
                self._check_db_equal()

    def test_update(self):
        notes2 = get_table(self.db_read, "notes")
        notes = get_table(self.db_read, "notes")
        for mode in ["update", "replace", "append"]:
            with self.subTest(mode=mode):
                self._reset()
                notes2.loc[notes2["id"] == 1555579337683, "tags"] = \
                    "definitelynew!"
                set_table(self.db_write, notes2, "notes", mode)
                if mode == "append":
                    self._check_db_equal()
                else:
                    notes2r = get_table(self.db_write, "notes")
                    chtag = notes2r.loc[notes2r["id"] == 1555579337683, "tags"]
                    self.assertListEqual(
                        list(chtag.values.tolist()),
                        ["definitelynew!"]
                    )
                    unchanged = notes.loc[notes["id"] != 1555579337683, :]
                    unchanged2 = notes2r.loc[notes2["id"] != 1555579337683, :]

                    self.assertListEqual(
                        list(unchanged.values.tolist()),
                        list(unchanged2.values.tolist())
                    )

    def test_update_append_does_not_delete(self):
        notes = get_table(self.db_read, "notes")
        cards = get_table(self.db_read, "cards")
        revs = get_table(self.db_read, "revs")
        notes.drop(notes.index)
        cards.drop(cards.index)
        revs.drop(revs.index)
        for mode in ["update", "append"]:
            with self.subTest(mode=mode):
                self._reset()
                set_table(self.db_write, notes, "notes", mode)
                set_table(self.db_write, cards, "cards", mode)
                set_table(self.db_write, revs, "revs", mode)
                self._check_db_equal()

    def test_replace_deletes(self):
        notes = get_table(self.db_read, "notes")
        cards = get_table(self.db_read, "cards")
        revs = get_table(self.db_read, "revs")
        notes = notes.drop(notes.index)
        cards = cards.drop(cards.index)
        revs = revs.drop(revs.index)
        self._reset()
        set_table(self.db_write, notes, "notes", "replace")
        set_table(self.db_write, cards, "cards", "replace")
        set_table(self.db_write, revs, "revs", "replace")
        notes = get_table(self.db_write, "notes")
        cards = get_table(self.db_write, "cards")
        revs = get_table(self.db_write, "revs")
        self.assertEqual(len(notes), 0)
        self.assertEqual(len(revs), 0)
        self.assertEqual(len(cards), 0)


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
