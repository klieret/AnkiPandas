#!/usr/bin/env python3

# std
import pathlib
import shutil

# 3rd
import pytest

# ours
from ankipandas.collection import Collection
from ankipandas.test.util import parameterized_paths


def _init_all_tables(col: Collection) -> None:
    """ Access all attributes at least once to ensure that they are
    initialized.
    """
    _ = col.notes
    _ = col.cards
    _ = col.revs


# Summarize changes
# ==========================================================================


@parameterized_paths()
def test_summarize_changes_uninitialized(db_path):
    col = Collection(db_path)
    sc = col.summarize_changes(output="dict")
    assert len(sc) == 0


@parameterized_paths()
def test_summarize_changes_no_changes(db_path):
    col = Collection(db_path)
    _init_all_tables(col)
    col.summarize_changes()
    sc = col.summarize_changes(output="dict")
    for item in ["cards", "revs", "notes"]:
        assert sc[item]["n_modified"] == 0
        assert sc[item]["n_added"] == 0
        assert sc[item]["n_deleted"] == 0
        assert sc[item]["has_changed"] == False


@parameterized_paths()
def test_summarize_notes_changed(db_path):
    col = Collection(db_path)
    col.notes.add_tag("this_will_be_modified", inplace=True)
    sc = col.summarize_changes(output="dict")
    assert sc["notes"]["n_modified"] == sc["notes"]["n"]


# Writing
# ==========================================================================


@parameterized_paths()
def test_read_write_identical_trivial(db_path, tmpdir):
    db_path = shutil.copy2(str(db_path), str(tmpdir))
    (pathlib.Path(str(tmpdir)) / "backups").mkdir()
    col = Collection(db_path)
    col.write(modify=True, delete=True, add=True)
    col_rel = Collection(db_path)
    assert col.notes.equals(col_rel.notes)
    assert col.cards.equals(col_rel.cards)
    assert col.revs.equals(col_rel.revs)


@parameterized_paths()
def test_write_raises_delete(db_path, tmpdir):
    db_path = shutil.copy2(str(db_path), str(tmpdir))
    (pathlib.Path(str(tmpdir)) / "backups").mkdir()
    col = Collection(db_path)
    col.notes.drop(col.notes.index, inplace=True)
    cases = [
        dict(modify=False, add=True),
        dict(modify=True, add=False),
        dict(modify=True, add=True),
    ]
    for case in cases:
        with pytest.raises(ValueError, match=".*would be deleted.*"):
            col.write(**case, delete=False)


@parameterized_paths()
def test_write_raises_modified(db_path, tmpdir):
    db_path = shutil.copy2(str(db_path), str(tmpdir))
    (pathlib.Path(str(tmpdir)) / "backups").mkdir()
    col = Collection(db_path)
    col.notes.add_tag("test", inplace=True)
    cases = [
        dict(add=False, delete=True),
        dict(add=True, delete=False),
        dict(add=True, delete=True),
    ]
    for case in cases:
        with pytest.raises(ValueError, match=".*would be modified.*"):
            col.write(**case, modify=False)


@parameterized_paths()
def test_write_raises_added(db_path, tmpdir):
    db_path = shutil.copy2(str(db_path), str(tmpdir))
    (pathlib.Path(str(tmpdir)) / "backups").mkdir()
    col = Collection(db_path)
    col.notes.add_note("Basic", ["test", "back"], inplace=True)
    cases = [
        dict(modify=False, delete=True),
        dict(modify=True, delete=False),
        dict(modify=True, delete=True),
    ]
    for case in cases:
        with pytest.raises(ValueError, match=".*would be modified.*"):
            col.write(**case, add=False)
