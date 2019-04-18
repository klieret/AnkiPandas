#!/usr/bin/env python3

""" Convenience functions that allow to load pandas dataframe with all the
desired columns in just one line of code."""

# std
import os
import collections
import pathlib
import pandas as pd
from functools import lru_cache
from typing import Iterable

# ours
import ankipandas.core_functions as apd


# todo: automatically find database
def load_notes(
    path,
    expand_fields=True
) -> pd.DataFrame:
    """
    Load all ntoes as a pandas DataFrame.

    Args:
        path: Path to database
        expand_fields: Add all fields as a new column

    Returns:
        Pandas dataframe
    """
    db = apd.load_db(path)
    df = apd.get_notes(db)
    apd.add_model_names(db, df, inplace=True)
    if expand_fields:
        apd.add_fields_as_columns(db, df, inplace=True)
    return df


# todo: automatically find database
def load_cards(
    path,
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
    db = apd.load_db(path)
    df = apd.get_cards(db)
    apd.add_deck_names(db, df, inplace=True)
    if merge_notes:
        apd.merge_note_info(db, df, inplace=True)
        apd.add_model_names(db, df, inplace=True)
    if expand_fields:
        apd.add_fields_as_columns(db, df, inplace=True)
    apd.close_db(db)
    return df


# todo: automatically find database
def load_revs(
    path,
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
    db = apd.load_db(path)
    df = apd.get_revlog(db)
    if merge_cards:
        apd.merge_card_info(db, df, inplace=True)
    if merge_notes:
        apd.add_nids(db, df, id_column="cid", inplace=True)
        apd.merge_note_info(db, df, inplace=True)
        if expand_fields:
            apd.add_fields_as_columns(db, df, inplace=True)
    apd.close_db(db)
    return df


@lru_cache(32)
def _find_database(search_path, maxdepth=6, filename="collection.anki2",
                   break_on_first=False, user=None):
    if not os.path.exists(str(search_path)):
        return collections.defaultdict(list)
    found = collections.defaultdict(list)
    for root, dirs, files in os.walk(str(search_path)):
        if filename in files:
            if user and not os.path.basename(root) == user:
                continue
            user = os.path.basename(root)
            found[user].append(pathlib.Path(root) / filename)
            if break_on_first:
                break
        if root.count(os.sep) >= maxdepth:
            del dirs[:]
    return found


@lru_cache(32)
def find_database(
        search_paths=None,
        maxdepth=8,
        filename="collection.anki2",
        user=None,
        break_on_first=True,
        quiet=False
):
    if not search_paths:
        # todo: rather use log
        if not quiet:
            print("Searching for database. This might take some time. "
                  "You can speed this up by specifying a search path or "
                  "directly entering the path to your database.")
        # todo: Windows paths?
        search_paths = [
            "~/.local/share/Anki2/",
            "~/Documents/Anki2",
            "~/Anki2/",
            pathlib.Path.home()
        ]
    if not isinstance(search_paths, Iterable):
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
        if found and break_on_first:
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
        else:
            found = list(found.values())
    if len(found) >= 2:
        raise ValueError(
            "Found more than one database belonging to user {} at {}".format(
                user,
                ", ".join(found)
            )
        )
    elif len(found) == 0:
        raise ValueError(
            "No database found. You might increase the search depth or specify "
            "search paths to find more."
        )
    found = found[0]
    return found


def table_help():
    """
    Return a pandas dataframe containing descriptions of every field in the
    anki database.

    """
    help_path = pathlib.Path(__file__).parent / "anki_fields.csv"
    df = pd.read_csv(help_path)
    return df
