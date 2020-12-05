#!/usr/bin/env python3

# std
import collections
import unittest
import tempfile
from typing import List
from pathlib import Path

# 3rd
from randomfiletree import sample_random_elements, iterative_gaussian_tree

# ours
import ankipandas.paths as paths
from ankipandas.util.misc import flatten_list_list
from ankipandas.util.log import set_debug_log_level


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
    for d in sample_random_elements(
        basedir, n_dirs=n, n_files=0, onfail="ignore"
    )[0]:
        p = Path(d) / filename
        p.touch()
        files.add(p)
    return list(files)


class TestFindDatabase(unittest.TestCase):
    def setUp(self):
        set_debug_log_level()
        self.dirs = {
            "nothing": tempfile.TemporaryDirectory(),
            "multiple": tempfile.TemporaryDirectory(),
            "perfect": tempfile.TemporaryDirectory(),
        }
        for d in self.dirs.values():
            iterative_gaussian_tree(
                d.name,
                repeat=5,
                nfolders=3,
                min_folders=1,
                nfiles=2,
                min_files=1,
                maxdepth=4,
            )
        self.dbs = {
            "nothing": [],
            "multiple": touch_file_in_random_folders(
                self.dirs["multiple"].name, "collection.anki2", 10
            ),
            "perfect": touch_file_in_random_folders(
                self.dirs["perfect"].name, "collection.anki2", 1
            ),
        }
        self.maxDiff = None

    def test_db_path_input_nexist(self):
        with self.assertRaises(FileNotFoundError):
            paths.db_path_input("/x/y/z")

    def test_db_path_input_multiple(self):
        with self.assertRaises(ValueError):
            paths.db_path_input(self.dirs["multiple"].name)

    def test_db_path_input_nothing(self):
        with self.assertRaises(ValueError):
            paths.db_path_input(self.dirs["nothing"].name)

    def test_db_path_input_perfect(self):
        self.assertEqual(
            paths.db_path_input(self.dirs["perfect"].name),
            self.dbs["perfect"][0],
        )

    def test__find_database(self):
        for d in self.dirs:
            a = sorted(
                map(
                    str,
                    flatten_list_list(
                        paths._find_db(
                            self.dirs[d].name,
                            maxdepth=None,
                            break_on_first=False,
                        ).values()
                    ),
                )
            )
            b = sorted(map(str, self.dbs[d]))
            self.assertListEqual(a, b)

    def test__find_database_filename(self):
        # If doesn't exist
        self.assertEqual(
            paths._find_db(
                Path("abc/myfilename.txt"), filename="myfilename.txt"
            ),
            {},
        )
        tmpdir = tempfile.TemporaryDirectory()
        dir_path = Path(tmpdir.name) / "myfolder"
        file_path = dir_path / "myfilename.txt"
        dir_path.mkdir()
        file_path.touch()
        self.assertEqual(
            paths._find_db(file_path, filename="myfilename.txt"),
            collections.defaultdict(list, {"myfolder": [file_path]}),
        )
        tmpdir.cleanup()

    def test_find_database(self):
        with self.assertRaises(ValueError):
            paths.find_db(self.dirs["nothing"].name, break_on_first=False)
        with self.assertRaises(ValueError):
            paths.find_db(self.dirs["multiple"].name, break_on_first=False)
            print(self.dbs["multiple"])
        self.assertEqual(
            str(paths.find_db(self.dirs["perfect"].name, break_on_first=False)),
            str(self.dbs["perfect"][0]),
        )

    def tearDown(self):
        for d in self.dirs.values():
            d.cleanup()


class TestBackup(unittest.TestCase):
    def setUp(self):
        set_debug_log_level()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmpdir_path = Path(self.tmpdir.name)
        (self.tmpdir_path / "collection.anki2").touch()
        (self.tmpdir_path / "backups").mkdir()

        self.tmpdir_only_db = tempfile.TemporaryDirectory()
        self.tmpdir_only_db_path = Path(self.tmpdir_only_db.name)
        (self.tmpdir_only_db_path / "collection.anki2").touch()

    def tearDown(self):
        self.tmpdir.cleanup()
        self.tmpdir_only_db.cleanup()

    def test_get_anki_backup_folder(self):
        self.assertEqual(
            str(
                paths.get_anki_backup_folder(
                    self.tmpdir_path / "collection.anki2"
                )
            ),
            str(self.tmpdir_path / "backups"),
        )

    def test_get_anki_backup_folder_raise(self):
        with self.assertRaises(FileNotFoundError):
            paths.get_anki_backup_folder(self.tmpdir_path / "asdf")
        with self.assertRaises(ValueError):
            paths.get_anki_backup_folder(
                self.tmpdir_only_db_path / "collection.anki2"
            )
        paths.get_anki_backup_folder(
            self.tmpdir_only_db_path / "collection.anki2", nexist="ignore"
        )

    def test_backup_db_auto(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "collection.anki2"
            db_path.touch()
            backup_folder = db_path.parent / "backups"
            backup_folder.mkdir()
            backup_path = paths.backup_db(db_path)
            self.assertTrue(backup_path.is_file())
            self.assertTrue(backup_path.parent == backup_folder)

    def test_backup_db_custom(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "collection.anki2"
            db_path.touch()
            backup_folder = db_path.parent / "myfolder"
            backup_path = paths.backup_db(db_path, backup_folder=backup_folder)
            self.assertTrue(backup_path.is_file())
            self.assertTrue(backup_path.parent == backup_folder)


if __name__ == "__main__":
    unittest.main()
