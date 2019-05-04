#!/usr/bin/env python3

# std
import collections
import unittest
from pathlib import Path
import tempfile
from typing import List, Any

# 3rd
from randomfiletree import sample_random_elements, iterative_gaussian_tree

# ours
import ankipandas.convenience_functions as convenience
from ankipandas.data.columns import *


def touch_file_in_random_folders(basedir, filename: str, n=1) -> List[Path]:
    """ Create files in random folders.

    Args:
        basedir: Starting directory
        filename: Filename of the files to create
        n: Number of files to create

    Returns:
        List of files that were created.
    """
    files = set()
    for d in sample_random_elements(basedir, n_dirs=n, n_files=0,
                                    onfail="ignore")[0]:
        p = Path(d) / filename
        p.touch()
        files.add(p)
    return list(files)


def flatten_list(lst: List[List[Any]]) -> List[Any]:
    """ Takes a list of lists and returns a list of all elements.

    Args:
        lst: List of Lists

    Returns:
        list
    """
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

    def test_db_path_input_nexist(self):
        with self.assertRaises(FileNotFoundError):
            convenience.db_path_input("/x/y/z")

    def test_db_path_input_multiple(self):
        with self.assertRaises(ValueError):
            convenience.db_path_input(self.dirs["multiple"].name)

    def test_db_path_input_nothing(self):
        with self.assertRaises(ValueError):
            convenience.db_path_input(self.dirs["nothing"].name)

    def test_db_path_input_perfect(self):
        self.assertEqual(
            convenience.db_path_input(self.dirs["perfect"].name),
            self.dbs["perfect"][0]
        )

    def test__find_database(self):
        for d in self.dirs:
            a = sorted(map(str, flatten_list(
                convenience._find_db(
                    self.dirs[d].name, maxdepth=None, break_on_first=False
                ).values()
            )))
            b = sorted(map(str, self.dbs[d]))
            self.assertListEqual(a, b)

    def test__find_database_filename(self):
        # If doesn't exist
        self.assertEqual(
            convenience._find_db(
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
            convenience._find_db(file_path, filename="myfilename.txt"),
            collections.defaultdict(list, {"myfolder": [file_path]})
        )
        tmpdir.cleanup()

    def test_find_database(self):
        with self.assertRaises(ValueError):
            convenience.find_db(
                self.dirs["nothing"].name, break_on_first=False
            )
        with self.assertRaises(ValueError):
            convenience.find_db(
                self.dirs["multiple"].name, break_on_first=False
            )
            print(self.dbs["multiple"])
        self.assertEqual(
            str(convenience.find_db(
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
            ["Column", "Table", "Description", "Native"]
        )
        self.assertGreater(
            len(df),
            10
        )

    def test_table_help_search_table(self):
        for table in ["notes", "cards", "revlog"]:
            with self.subTest(table=table):
                df = convenience.table_help(table=table, native=True)
                self.assertListEqual(
                    sorted(list(df["Column"].unique())),
                    columns[table]
                )

    def test_table_help_search_column(self):
        for table in ["notes", "cards", "revlog"]:
            with self.subTest(table=table):
                df = convenience.table_help(table=table, column="id")
                df2 = convenience.table_help(
                    table=table, column="id", native=False
                )
                self.assertEqual(len(df), 1)
                self.assertEqual(len(df2), 0)


class TestLoaders(unittest.TestCase):
    def setUp(self):
        self.path = Path(__file__).parent / "data" / "few_basic_cards" / \
                    "collection.anki2"

    def test_load_notes_no_expand(self):
        notes = convenience.load_notes(self.path, expand_fields=False)
        self.assertEqual(
            sorted(list(notes.columns)),
            sorted(columns["notes"] + ["mname"])
        )

    def test_load_notes_expand(self):
        notes = convenience.load_notes(self.path, expand_fields=True)
        self.assertEqual(
            sorted(list(notes.columns)),
            sorted(columns["notes"] + ["mname", "Front", "Back"])
        )

    def test_load_cards(self):
        cards = convenience.load_cards(self.path)
        self.assertEqual(
            sorted(list(cards.columns)),
            sorted(list(set(
                columns["cards"] + columns["notes"] +
                ["dname", "mname", "Front", "Back"] +
                ["ndata", "nflags", "nmod", "nusn"]
            )))  # clashes
        )

    def test_load_cards_nomerge(self):
        cards = convenience.load_cards(self.path, merge_notes=False)
        self.assertEqual(
            sorted(list(cards.columns)),
            sorted(columns["cards"] + ["dname"])
        )

    def test_load_revs(self):
        revs = convenience.load_revs(self.path)
        self.assertEqual(
            sorted(list(revs.columns)),
            sorted(list(set(
                columns["revlog"] + columns["cards"] + columns["notes"] +
                ["dname", "mname", "Front", "Back"] +
                ["ndata", "nflags", "nmod", "nusn"] +
                ["civl", "cfactor", "cusn", "ctype"]
            )))
        )

    def test_load_revs_nomerge(self):
        revs = convenience.load_revs(self.path, merge_cards=False,
                                     merge_notes=False)
        self.assertEqual(
            sorted(list(revs.columns)),
            sorted(columns["revlog"])
        )


if __name__ == "__main__":
    unittest.main()
