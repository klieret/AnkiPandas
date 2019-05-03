#!/usr/bin/env python3

# std
import collections
import unittest
from pathlib import Path
import tempfile

# 3rd
from randomfiletree import sample_random_elements, iterative_gaussian_tree

# ours
import ankipandas.convenience_functions as convenience
from ankipandas.test.shared import *


# todo: doc, perhaps move to RandomFileTree package?
def touch_file_in_random_folders(basedir, filename, n=1):
    files = set()
    for d in sample_random_elements(basedir, n_dirs=n, n_files=0,
                                    onfail="ignore")[0]:
        p = Path(d) / filename
        p.touch()
        files.add(p)
    return list(files)


# todo: doc
def flatten_list(lst):
    return [item for sublist in lst for item in sublist]


class TestFindDatabase(unittest.TestCase):
    def setUp(self):
        self.dirs = {
            "nothing": tempfile.TemporaryDirectory(),
            "multiple": tempfile.TemporaryDirectory(),
            "perfect": tempfile.TemporaryDirectory()
        }
        for d in self.dirs.values():
            iterative_gaussian_tree(
                d.name,
                repeat=5,
                nfolders=1,
                min_folders=1,
                nfiles=2,
                min_files=1,
            )
        self.dbs = {
            "nothing": [],
            "multiple": touch_file_in_random_folders(
                self.dirs["multiple"].name, "collection.anki2", 10),
            "perfect":  touch_file_in_random_folders(
                self.dirs["perfect"].name, "collection.anki2", 1)
        }
        self.maxDiff = None

    def test__find_database(self):
        for d in self.dirs:
            a = sorted(map(str, flatten_list(
                convenience._find_database(
                    self.dirs[d].name, maxdepth=None, break_on_first=False
                ).values()
            )))
            b = sorted(map(str, self.dbs[d]))
            self.assertListEqual(a, b)

    def test__find_database_filename(self):
        # If doesn't exist
        self.assertEqual(
            convenience._find_database(
                Path("abc/myfilename.txt"), filename="myfilename.txt"
            ),
            {}
        )
        tmpdir = tempfile.TemporaryDirectory()
        dir_path = Path(tmpdir.name) / "myfolder"
        file_path = dir_path / "myfilename.txt"
        dir_path.mkdir()
        file_path.touch()
        self.assertEqual(
            convenience._find_database(file_path, filename="myfilename.txt"),
            collections.defaultdict(list, {"myfolder": [file_path]})
        )
        tmpdir.cleanup()

    def test_find_database(self):
        with self.assertRaises(ValueError):
            convenience.find_database(
                self.dirs["nothing"].name, break_on_first=False
            )
        with self.assertRaises(ValueError):
            convenience.find_database(
                self.dirs["multiple"].name, break_on_first=False
            )
            print(self.dbs["multiple"])
        self.assertEqual(
            str(convenience.find_database(
                self.dirs["perfect"].name, break_on_first=False
            )),
            str(self.dbs["perfect"][0])
        )

    def tearDown(self):
        for d in self.dirs.values():
            d.cleanup()


class TestHelp(unittest.TestCase):
    def test_table_help(self):
        df = convenience.table_help()
        self.assertListEqual(
            list(df.columns),
            ["Name", "Tables", "Description", "Native"]
        )
        self.assertGreater(
            len(df),
            10
        )


class TestLoaders(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).parent / "data" / "few_basic_cards" / \
                    "collection.anki2"

    def test_load_notes_no_expand(self):
        notes = convenience.load_notes(self.path, expand_fields=False)
        self.assertEqual(
            sorted(list(notes.columns)),
            sorted(note_cols + ["mname"])
        )

    def test_load_notes_expand(self):
        notes = convenience.load_notes(self.path, expand_fields=True)
        self.assertEqual(
            sorted(list(notes.columns)),
            sorted(note_cols + ["mname", "Front", "Back"])
        )

    def test_load_cards(self):
        cards = convenience.load_cards(self.path)
        self.assertEqual(
            sorted(list(cards.columns)),
            sorted(list(set(
                card_cols + note_cols + ["dname", "mname", "Front", "Back"] +
                ["ndata", "nflags", "nmod", "nusn"]
            )))  # clashes
        )

    def test_load_cards_nomerge(self):
        cards = convenience.load_cards(self.path, merge_notes=False)
        self.assertEqual(
            sorted(list(cards.columns)),
            sorted(card_cols + ["dname"])
        )


if __name__ == "__main__":
    unittest.main()
