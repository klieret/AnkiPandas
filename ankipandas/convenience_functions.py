#!/usr/bin/env python3

""" Convenience functions that allow to load pandas dataframe with all the
desired columns in just one line of code."""

# std
import os
import collections
import pathlib
import pandas as pd
from functools import lru_cache

# ours
import ankipandas.core_functions as apd
from ankipandas.util.log import get_logger


def load_notes(
    path=None,
    expand_fields=True
) -> pd.DataFrame:
    """
    Load all notes as a pandas DataFrame.

    Args:
        path: Path to database
        expand_fields: Add all fields as a new column

    Returns:
        Pandas dataframe
    """
    if not path:
        path = find_database()
    db = apd.load_db(path)
    df = apd.get_notes(db)
    apd.add_mnames(db, df, inplace=True)
    if expand_fields:
        apd.add_fields_as_columns(db, df, inplace=True)
    return df


def load_cards(
    path=None,
    merge_notes=True,
    expand_fields=True
) -> pd.DataFrame:
    """
    Return all cards as a pandas DataFrame.

    Args:
        path: Path to database
        merge_notes: Merge information from the notes (default True), e.g. all
            of the fields.
        expand_fields: When merging notes, epxand the 'flds' column to have a
            column for every field.
    Returns:
        Pandas dataframe
    """
    if not path:
        path = find_database()
    db = apd.load_db(path)
    df = apd.get_cards(db)
    apd.add_dnames(db, df, inplace=True)
    if merge_notes:
        apd.merge_notes(db, df, inplace=True)
        apd.add_mnames(db, df, inplace=True)
        if expand_fields:
            apd.add_fields_as_columns(db, df, inplace=True)
    apd.close_db(db)
    return df


def load_revs(
    path=None,
    merge_cards=True,
    merge_notes=True,
    expand_fields=True
) -> pd.DataFrame:
    """
    Load revision log as a pandas DataFrame

    Args:
        path: Path to database
        merge_cards: Merge information from the cards
        merge_notes: Merge information from the notes (default True), e.g. all
            of the fields.
        expand_fields: When merging notes, epxand the 'flds' column to have a
            column for every field.

    Returns:
        Pandas dataframe
    """
    if not path:
        path = find_database()
    db = apd.load_db(path)
    df = apd.get_revlog(db)
    if merge_cards:
        apd.merge_cards(db, df, inplace=True)
    if merge_notes:
        apd.add_nids(db, df, cid_column="cid", inplace=True)
        apd.merge_notes(db, df, inplace=True)
        if expand_fields:
            apd.add_fields_as_columns(db, df, inplace=True)
    apd.close_db(db)
    return df


# todo: decorator messes up sphinx signature
@lru_cache(32)
def _find_database(search_path, maxdepth=6,
                   filename="collection.anki2",
                   break_on_first=False, user=None):
    """
    Like find_database but only for one search path at a time. Also doesn't
    raise any error, even if the search path doesn't exist.

    Returns:
        collection.defaultdict({user: [list of results]})
    """
    search_path = pathlib.Path(search_path)
    if not os.path.exists(str(search_path)):
        return collections.defaultdict(list)
    if search_path.is_file():
        if search_path.name == filename:
            return collections.defaultdict(
                list, {search_path.parent.name: [search_path]}
            )
    found = collections.defaultdict(list)
    for root, dirs, files in os.walk(str(search_path)):
        if filename in files:
            _user = os.path.basename(root)
            if user and not _user == user:
                continue
            found[_user].append(pathlib.Path(root) / filename)
            if break_on_first:
                break
        if maxdepth and root.count(os.sep) >= maxdepth:
            del dirs[:]
    return found


# todo: decorator messes up sphinx signature
@lru_cache(32)
def find_database(
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
        :class:`ValueError` if none ore more than one result is found.

    Returns:
        pathlib.Path to the anki2 database
    """
    if not search_paths:
        get_logger().info(
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
    if isinstance(search_paths, (str, pathlib.PurePath)):
        search_paths = [search_paths]
    found = {}
    for search_path in search_paths:
        found = {
            **found,
            **_find_database(
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
    get_logger().debug("Database found at '{}'.".format(found))
    return found


def table_help(table=None, columns=None, native=None) -> pd.DataFrame:
    """
    Return a pandas dataframe containing descriptions of every field in the
    anki database.

    Args:
        table: notes, cards, revlog
        columns: Which fields/columns are you looking for?
        native: If true, only columns that are present in the official anki
            columns are shown.

    Returns:
        Pandas DataFrame with all matches.
    """
    help_path = pathlib.Path(__file__).parent / "data" / "anki_fields.csv"
    df = pd.read_csv(help_path)
    df["Tables"] = df["Tables"].str.split(", ")
    if table:
        df = df.loc[df["Tables"].apply(lambda t: table in t), :]
    if isinstance(columns, str):
        columns = [columns]
    if columns:
        df = df[df["Name"].isin(columns)]
    if native is not None:
        df = df.query("Native=={}".format(native))

    return df
