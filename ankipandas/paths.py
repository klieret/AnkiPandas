#!/usr/bin/env python3

""" Convenience functions to find the database and other system locations
without the user having to specify full paths.
"""

# std
import os
import collections
import datetime
import pathlib
from functools import lru_cache
import shutil
from typing import Union

# ours
from ankipandas.util.log import log


@lru_cache(32)
def _find_db(search_path, maxdepth=6,
             filename="collection.anki2",
             break_on_first=False, user=None):
    """
    Like find_database but only for one search path at a time. Also doesn't
    raise any error, even if the search path doesn't exist.

    Returns:
        collection.defaultdict({user: [list of results]})
    """
    search_path = pathlib.Path(search_path)
    if not search_path.exists():
        log.debug(
            "_find_db: Search path '{}' does not "
            "exist.".format(str(search_path))
        )
        return collections.defaultdict(list)
    if search_path.is_file():
        if search_path.name == filename:
            return collections.defaultdict(
                list, {search_path.parent.name: [search_path]}
            )
        else:
            log.warning(
                "_find_db: Search path '{}' is a file, but filename does not "
                "match that of '{}'.".format(str(search_path), filename)
            )
            return collections.defaultdict(list)
    found = collections.defaultdict(list)
    for root, dirs, files in os.walk(str(search_path)):
        if filename in files:
            _user = os.path.basename(root)
            if user and not _user == user:
                continue
            found[_user].append(pathlib.Path(root) / filename)
            if break_on_first:
                log.debug("_find_db: Breaking after first hit.")
                break
        if maxdepth and root.count(os.sep) >= maxdepth:
            log.debug(
                "_find_db: Abort search at '{}'. "
                "Max depth exceeded.".format(str(root))
            )
            del dirs[:]
    return found


@lru_cache(32)
def find_db(
        search_paths=None,
        maxdepth=8,
        filename="collection.anki2",
        user=None,
        break_on_first=True,
) -> pathlib.Path:
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
        If none ore more than one result is found: :class:`ValueError`

    Returns:
        pathlib.Path to the anki2 database
    """
    if not search_paths:
        log.info(
            "Searching for database. This might take some time. "
            "You can speed this up by specifying a search path or "
            "directly entering the path to your database."
        )
        # todo: Windows paths?
        search_paths = [
            "~/.local/share/Anki2/",
            "~/Documents/Anki2",
            "~/Anki2/",
            pathlib.Path.home()
        ]
    if break_on_first:
        log.warning(
            "The search will stop at the first hit, so please verify that "
            "the result is correct (for example in case there might be more"
            "than one Anki installations)"
        )
    if isinstance(search_paths, (str, pathlib.PurePath)):
        search_paths = [search_paths]
    found = {}
    for search_path in search_paths:
        found = {
            **found,
            **_find_db(
                search_path,
                maxdepth=maxdepth,
                filename=filename,
                user=user,
                break_on_first=break_on_first
            )
        }
        if break_on_first:
            if user is not None:
                if user in found:
                    break
            else:
                if found:
                    break

    if user:
        if user not in found:
            raise ValueError(
                "Could not find database belonging to user {}".format(user)
            )
        found = found[user]
    else:
        if len(found.keys()) >= 2:
            raise ValueError(
                "Found databases for more than one user: {}. Please specify "
                "the user.".format(
                    ", ".join(found.keys())
                )
            )
        elif len(found.keys()) == 0:
            raise ValueError(
                "No database found. You might increase the search depth or "
                "specify search paths to find more."
            )
        else:
            found = list(found.values())[0]
    if len(found) >= 2:
        raise ValueError(
            "Found more than one database belonging to user {} at {}".format(
                user,
                ", ".join(found)
            )
        )
    found = found[0]
    log.debug("Database found at '{}'.".format(found))
    return found


@lru_cache(32)
def db_path_input(path: Union[str, pathlib.PurePath] = None,
                  user: str = None) -> pathlib.Path:
    """ Helper function to interpret user input of path to database.

    1. If no path is given, we search through some default locations
    2. If path points to a file: Take that file
    3. If path points to a directory: Search in that directory

    Args:
        path: Path to database or search path or None
        user: User name of anki collection or None

    Returns:
        Path to anki database as :class:`pathlib.Path` object

    Raises:
        If path does not exist: :class:`FileNotFoundError`
        In various other cases: :class:`ValueError`
    """
    if path is None:
        result = find_db(user=user)
    else:
        path = pathlib.Path(path)
        if not path.exists():
            raise FileNotFoundError(
                "db_path_input: File '{}' does not exist.".format(str(path))
            )
        if path.is_file():
            log.debug(
                "db_path_input: Database explicitly set to '{}'.".format(path)
            )
            result = path
        else:
            result = find_db(
                search_paths=(path,),
                user=user,
                break_on_first=False
            )
            log.info(
                "Database found at '{}'.".format(result)
            )
    if result:
        return result
    else:
        raise ValueError("Database could not be found.")


def db_backup_file_name() -> str:
    """ Time based file name of the backup file. """
    return "backup-ankipandas-{}.anki2".format(
        datetime.datetime.now().strftime("%Y-%m-%d-%H.%M.%S.%f")
    )


def get_anki_backup_folder(
        path: Union[str, pathlib.PurePath],
        nexist="raise") -> pathlib.Path:
    """ Return path to Anki backup folder.

    Args:
        path: Path to Aki database as :class:`pathlib.Path`
        nexist: What to do if backup folder doesn't seem to exist: ``raise`` or
            ``ignore``.

    Returns:
        Path to Anki backup folder as :class:`pathlib.Path`.
    """
    path = pathlib.Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            "Database path {} seems to be invalid.".format(path)
        )
    backup_folder = path.parent / "backups"
    if nexist == "raise" and not backup_folder.is_dir():
        raise ValueError(
            "Anki backup folder corresponding to database at {} doesn't seem"
            " to exist. Perhaps you can specify a custom back "
            "folder?".format(path)
        )
    return backup_folder


def backup_db(db_path: Union[str, pathlib.PurePath],
              backup_folder: Union[str, pathlib.PurePath] = None) \
        -> pathlib.Path:
    """
    Back up database file.

    Args:
        db_path: Path to database
        backup_folder: Path to backup folder. If None is given, the backup is
            created in the Anki backup directory.

    Returns:
        Path to newly created backup file as :class:`pathlib.Path`.
    """
    db_path = pathlib.Path(db_path)
    if backup_folder:
        backup_folder = pathlib.Path(backup_folder)
        if not backup_folder.is_dir():
            log.debug("Creating backup directory {}".format(str(backup_folder)))
            backup_folder.mkdir(parents=True)
    else:
        backup_folder = get_anki_backup_folder(db_path, nexist="raise")
    if not db_path.is_file():
        raise FileNotFoundError(
            "Database does not seem to exist."
        )
    backup_path = backup_folder / db_backup_file_name()
    shutil.copy2(str(db_path), str(backup_path))
    return backup_path
