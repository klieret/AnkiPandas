#!/usr/bin/env python3

# std
import unittest
from pathlib import Path
import tempfile
import random
import string
import os

# ours
import ankipandas.convenience_functions as convenience


def get_random_string(min_length=5, max_length=10):
    """
    Get a random string

    Args:
        min_length: Minimal length of string
        max_length: Maximal length of string

    Returns:
        Random string of ascii characters
    """
    length = random.randint(min_length, max_length)
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits)
        for _ in range(length)
    )


def create_random_tree(basedir, prob_file=0.9, prob_folder=0.5, repeat=1,
                       maxdepth=None):
    """
    Create a random set of files and folders by repeatedly walking through the
    current tree and creating random files or subfolders with a certain kind
    of probability

    Args:
        basedir: Directory to create files and folders in
        prob_file: Probability to create a file in a directory
        prob_folder: Probability to create a
        repeat: Walk this often through the directory tree to create new
            subdirectories and files
        maxdepth: Maximum depth to descend into current file tree

    Returns:
        None
    """
    for i in range(repeat):
        for root, dirs, files in os.walk(str(basedir)):
            if random.random() < prob_folder:
                p = Path(root) / get_random_string()
                p.mkdir(exist_ok=True)
            if random.random() < prob_file:
                p = Path(root) / get_random_string()
                p.touch(exist_ok=True)
            if maxdepth and root.count(os.sep) >= maxdepth:
                del dirs[:]


def select_random_folders(basedir, n=1):
    """
    Select random subfolders

    Args:
        basedir: Directory to scan
        n: Number of subfolders to return

    Returns:
        List of pathlib.Path objects
    """
    alldirs = []
    for root, dirs, files in os.walk(str(basedir)):
        for d in dirs:
            alldirs.append(Path(root) / d)
    if not alldirs:
        return []
    return [random.choice(alldirs) for _ in range(n)]


def touch_file_in_random_folders(basedir, filename, n=1):
    files = set()
    for d in select_random_folders(basedir, n=n):
        p = Path(d) / filename
        p.touch()
        files.add(p)
    return list(files)


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
            create_random_tree(d.name, repeat=5)
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
            a = sorted(map(str, flatten_list(convenience._find_database(self.dirs[d].name, maxdepth=None, break_on_first=False).values())))
            b = sorted(map(str, self.dbs[d]))
            self.assertListEqual(a, b)

    def test_find_database(self):
        with self.assertRaises(ValueError):
            convenience.find_database(self.dirs["nothing"].name, break_on_first=False)
        with self.assertRaises(ValueError):
            convenience.find_database(self.dirs["multiple"].name, break_on_first=False)
        self.assertEqual(
            str(convenience.find_database(self.dirs["perfect"].name, break_on_first=False)),
            str(self.dbs["perfect"][0])
        )

    def tearDown(self):
        for dir in self.dirs.values():
            dir.cleanup()


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


if __name__ == "__main__":
    unittest.main()
