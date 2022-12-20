""" Convenience functions to find the database and other system locations
without the user having to specify full paths.
"""

from __future__ import annotations

import collections
import datetime

# std
import os
import shutil
from functools import lru_cache
from pathlib import Path, PurePath
from typing import DefaultDict

# ours
from ankipandas.util.log import log


@lru_cache(32)
def _find_db(
    search_path,
    maxdepth=6,
    filename="collection.anki2",
    break_on_first=False,
    user: str | None = None,
) -> DefaultDict[str, list[Path]]:
    """
    Like find_database but only for one search path at a time. Also doesn't
    raise any error, even if the search path doesn't exist.

    Args:
        search_path:
        maxdepth: Maximum depth relative to search_path
        filename:
        break_on_first: Break on first search result
        user: Only search for this user

    Returns:
        collection.defaultdict({user: [list of results]})
    """
    search_path = Path(search_path)
    if not search_path.exists():
        log.debug("_find_db: Search path %r does not exist.", str(search_path))
        return collections.defaultdict(list)
    if search_path.is_file():
        if search_path.name == filename:
            return collections.defaultdict(
                list, {search_path.parent.name: [search_path]}
            )
        else:
            log.warning(
                "_find_db: Search path %r is a file, but filename does not "
                "match that of %r.",
                str(search_path),
                filename,
            )
            return collections.defaultdict(list)
    found: DefaultDict[str, list[Path]] = collections.defaultdict(list)
    for root, dirs, files in os.walk(str(search_path)):
        if filename in files:
            _user = os.path.basename(root)
            if user and not _user == user:
                continue
            found[_user].append(Path(root) / filename)
            if break_on_first:
                log.debug("_find_db: Breaking after first hit.")
                break
        depth = len(Path(root).relative_to(search_path).parts)
        if maxdepth and depth >= maxdepth:
            # log.debug(
            #     "_find_db: Abort search at %r. "
            #     "Max depth exceeded.",
            #     str(root)
            # )
            del dirs[:]
    return found


@lru_cache(32)
def find_db(
    search_paths=None,
    maxdepth=8,
    filename="collection.anki2",
    user=None,
    break_on_first=True,
) -> Path:
    """
    Find path to anki2 database.

    Args:
        search_paths: Search path as string or pathlib object or list/iterable
            thereof. If None, some search paths are set by default.
        maxdepth: Maximal search depth.
        filename: Filename of the collection (default: ``collections.anki2``)
        user: Username to which the collection belongs. If None, search for
            databases of any user.
        break_on_first: Stop searching once a database is found. This is
            obviously faster, but you will not get any errors if there are
            multiple databases matching your criteria.

    Raises:
        If none or more than one result is found: :class:`ValueError`

    Returns:
        Path to the anki2 database
    """
    if not search_paths:
        log.info(
            "Searching for database. This might take some time. "
            "You can speed this up by specifying a search path or "
            "directly entering the path to your database."
        )
        search_paths = [
            "~/.local/share/Anki2/",
            "~/Documents/Anki2",
            Path(os.getenv("APPDATA", "~") + "/Anki2/"),
            "~/.local/share/Anki2",
            Path.home(),
        ]
        search_paths = [Path(sp).expanduser().resolve() for sp in search_paths]
    if break_on_first:
        log.warning(
            "The search will stop at the first hit, so please verify that "
            "the result is correct (for example in case there might be more "
            "than one Anki installation)"
        )
    if isinstance(search_paths, (str, PurePath)):
        search_paths = [search_paths]
    found: dict[str, list[Path]] = {}
    for search_path in search_paths:
        found = {
            **found,
            **_find_db(
                search_path,
                maxdepth=maxdepth,
                filename=filename,
                user=user,
                break_on_first=break_on_first,
            ),
        }
        if break_on_first:
            if user is not None:
                if user in found:
                    break
            else:
                if found:
                    break

    if user:
        # We were searching for a specific user
        if user not in found:
            raise ValueError(
                f"Could not find database belonging to user {user}"
            )
        else:
            results_user = found[user]
    else:
        if len(found) >= 2:
            raise ValueError(
                "Found databases for more than one user: {}. Please specify "
                "the user.".format(", ".join(found))
            )
        elif not found:
            raise ValueError(
                "No database found. You might increase the search depth or "
                "specify search paths to find more."
            )
        else:
            # No user specified but we found only one
            results_user = found.popitem()[1]

    if len(results_user) >= 2:
        raise ValueError(
            "Found more than one database belonging to user {} at {}".format(
                user, ", ".join(map(str, results_user))
            )
        )

    assert len(results_user) == 1
    final_result = results_user[0]
    log.debug("Database found at %r.", final_result)
    return final_result


@lru_cache(32)
def db_path_input(
    path: str | PurePath | None = None, user: str | None = None
) -> Path:
    """Helper function to interpret user input of path to database.

    1. If no path is given, we search through some default locations
    2. If path points to a file: Take that file
    3. If path points to a directory: Search in that directory

    Args:
        path: Path to database or search path or None
        user: User name of anki collection or None

    Returns:
        Path to anki database as :class:`Path` object

    Raises:
        If path does not exist: :class:`FileNotFoundError`
        In various other cases: :class:`ValueError`
    """
    if path is None:
        result = find_db(user=user)
    else:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"db_path_input: File '{str(path)}' does not exist."
            )
        if path.is_file():
            log.debug(
                "db_path_input: Database explicitly set to %r.", str(path)
            )
            result = path
        else:
            result = find_db(
                search_paths=(path,), user=user, break_on_first=False
            )
            log.info("Database found at %r.", str(result))
    if result:
        return result
    else:
        raise ValueError("Database could not be found.")


def db_backup_file_name() -> str:
    """Time based file name of the backup file."""
    return "backup-ankipandas-{}.anki2".format(
        datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")
    )


def get_anki_backup_folder(path: str | PurePath, nexist="raise") -> Path:
    """Return path to Anki backup folder.

    Args:
        path: Path to Aki database as :class:`Path`
        nexist: What to do if backup folder doesn't seem to exist: ``raise`` or
            ``ignore``.

    Returns:
        Path to Anki backup folder as :class:`Path`.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Database path {path} seems to be invalid.")
    backup_folder = path.parent / "backups"
    if nexist == "raise" and not backup_folder.is_dir():
        raise ValueError(
            "Anki backup folder corresponding to database at {} doesn't seem"
            " to exist. Perhaps you can specify a custom back "
            "folder?".format(path)
        )
    return backup_folder


def backup_db(
    db_path: str | PurePath,
    backup_folder: str | PurePath | None = None,
) -> Path:
    """
    Back up database file.

    Args:
        db_path: Path to database
        backup_folder: Path to backup folder. If None is given, the backup is
            created in the Anki backup directory.

    Returns:
        Path to newly created backup file as :class:`Path`.
    """
    db_path = Path(db_path)
    if backup_folder:
        backup_folder = Path(backup_folder)
        if not backup_folder.is_dir():
            log.debug("Creating backup directory %s.", backup_folder)
            backup_folder.mkdir(parents=True)
    else:
        backup_folder = get_anki_backup_folder(db_path, nexist="raise")
    if not db_path.is_file():
        raise FileNotFoundError("Database does not seem to exist.")
    backup_path = backup_folder / db_backup_file_name()
    shutil.copy2(str(db_path), str(backup_path))
    return backup_path
