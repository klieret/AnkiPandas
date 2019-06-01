#!/usr/bin/env python3

# std
import pathlib
import unittest
import tempfile
import shutil

# ours
from ankipandas.collection import Collection


class TestCollection(unittest.TestCase):
    def setUp(self):
        self.db_path = (
            pathlib.Path(__file__).parent
            / "data"
            / "few_basic_cards"
            / "collection.anki2"
        )

        self.col = Collection(self.db_path)
        self.notes = self.col.notes
        self.cards = self.col.cards
        self.revs = self.col.revs

    # Summarize changes
    # ==========================================================================

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

    # Writing
    # ==========================================================================

    def test_read_write_identical_trivial(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = shutil.copy2(str(self.db_path), tmpdir)
            (pathlib.Path(tmpdir) / "backups").mkdir()
            col = Collection(db_path)
            col.write(modify=True, delete=True, add=True)
            col_rel = Collection(db_path)
            self.assertTrue(col.notes.equals(col_rel.notes))
            self.assertTrue(col.cards.equals(col_rel.cards))
            self.assertTrue(col.revs.equals(col_rel.revs))

    def test_write_raises_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = shutil.copy2(str(self.db_path), tmpdir)
            (pathlib.Path(tmpdir) / "backups").mkdir()
            col = Collection(db_path)
            col.notes.drop(col.notes.index, inplace=True)
            cases = [
                dict(modify=False, add=True),
                dict(modify=True, add=False),
                dict(modify=True, add=True),
            ]
            for case in cases:
                with self.subTest(**case):
                    with self.assertRaises(ValueError) as context:
                        col.write(**case, delete=False)
                    self.assertTrue(
                        "would be deleted" in str(context.exception)
                    )

    def test_write_raises_modified(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = shutil.copy2(str(self.db_path), tmpdir)
            (pathlib.Path(tmpdir) / "backups").mkdir()
            col = Collection(db_path)
            col.notes.add_tag("test", inplace=True)
            cases = [
                dict(add=False, delete=True),
                dict(add=True, delete=False),
                dict(add=True, delete=True),
            ]
            for case in cases:
                with self.subTest(**case):
                    with self.assertRaises(ValueError) as context:
                        col.write(**case, modify=False)
                    self.assertTrue(
                        "would be modified" in str(context.exception)
                    )

    def test_write_raises_added(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = shutil.copy2(str(self.db_path), tmpdir)
            (pathlib.Path(tmpdir) / "backups").mkdir()
            col = Collection(db_path)
            col.notes.add_note("Basic", ["test", "back"], inplace=True)
            cases = [
                dict(modify=False, delete=True),
                dict(modify=True, delete=False),
                dict(modify=True, delete=True),
            ]
            for case in cases:
                with self.subTest(**case):
                    with self.assertRaises(ValueError) as context:
                        col.write(**case, add=False)
                    self.assertTrue(
                        "would be modified" in str(context.exception)
                    )


if __name__ == "__main__":
    unittest.main()
