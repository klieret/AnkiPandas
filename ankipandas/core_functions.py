#!/usr/bin/env python3

""" Most of the actual implementation is done with these functions that allow
a finer control over what is happenin than the convenience functions.
"""

# std
import sqlite3
import json
import pathlib
from functools import lru_cache
import copy

# 3rd
import pandas as pd
import numpy as np

# ours
from ankipandas.util.dataframe import replace_df_inplace
from ankipandas.util.log import log
from ankipandas.columns import columns_anki2ours, tables_ours2anki

CACHE_SIZE = 32


# Open/Close db
# ==============================================================================

def load_db(path):
    """
    Load database from path

    Args:
        path: String or pathlib path.

    Returns:
        sqlite connection
    """
    path = pathlib.Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            "Not a file/file not found: {}".format(path)
        )
    return sqlite3.connect(str(path.resolve()))


def close_db(db: sqlite3.Connection) -> None:
    """ Close the database.

    Args:
        db:  Database (:class:`sqlite3.Connection`)

    Returns:
        None
    """
    db.close()


# Basic getters
# ==============================================================================

def get_table(db: sqlite3.Connection, table: str) -> pd.DataFrame:
    """ Get raw table from the Anki database.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        table: ``cards``, ``notes`` or ``revs``

    Returns:
        :class:`pandas.DataFrame`
    """

    df = pd.read_sql_query(
        "SELECT * FROM {}".format(tables_ours2anki[table]),
        db
    )
    return df


@lru_cache(CACHE_SIZE)
def get_info(db: sqlite3.Connection) -> dict:
    """
    Get all other information from the databse, e.g. information about models,
    decks etc.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Nested dictionary.
    """
    _df = pd.read_sql_query("SELECT * FROM col ", db)
    assert(len(_df) == 1)
    ret = {}
    for col in _df.columns:
        val = _df[col][0]
        if isinstance(val, str):
            ret[col] = json.loads(val)
        else:
            ret[col] = val
    return ret


# Basic Setters
# ==============================================================================

# fixme: Table names changed
# fixme: Need to change data types again
# fixme: need to pop first letters
# fixme: id_column is now dependent
def _set_table(db: sqlite3.Connection, df: pd.DataFrame, table: str,
               mode: str, id_column="id", same_columns=True,
               drop_new_columns=True
               ) -> None:
    """
    Write table back to database.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: The :class:`pandas.DataFrame` to write
        table: Table to write to: 'notes', 'cards', 'revlog'
        mode: 'update': Update only existing entries, 'append': Only append new
            entries, but do not modify, 'replace': Append, modify and delete
        same_columns: Check that the columns will stay exactly the same
        drop_new_columns: Drop any columns that are in the new dataframe
            but not in the old table.

    Returns:
        None
    """
    df_old = get_table(db, table)
    old_indices = set(df_old[id_column])
    new_indices = set(df[id_column])
    print("old indices", old_indices)
    print("new indices", new_indices)
    if mode == "update":
        indices = set(old_indices)
    elif mode == "append":
        indices = set(new_indices) - set(old_indices)
        if not indices:
            log.warning(
                "Was told to append to table, but there do not seem to be any"
                " new entries. Returning doing nothing."
            )
            return
    elif mode == "replace":
        indices = set(new_indices)
    else:
        raise ValueError("Unknown mode '{}'.".format(mode))
    # Remove everything not indices
    # fixme: Do we need to make a deepcopy?
    df = df[df[id_column].isin(indices)]
    old_cols = list(df_old.columns)
    new_cols = list(df.columns)
    if drop_new_columns:
        df.drop(set(new_cols) - set(old_cols), axis=1, inplace=True)
    if same_columns:
        if not set(df.columns) == set(df_old.columns):
            raise ValueError("Columns do not match: Old: {}, New: {}".format(
                ", ".join(df_old.columns), ", ".join(df.columns)
            ))
    if mode == "append":
        if_exists = "append"
    else:
        if_exists = "replace"
    df.to_sql(table, db, if_exists=if_exists, index=False)


# Trivially derived getters
# ==============================================================================

# todo: Using decorators here causes the function signatures to be messed up
#  with sphinx but oh well.

@lru_cache(CACHE_SIZE)
def get_deck_info(db: sqlite3.Connection):
    """ Get information about decks.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Nested dictionary
    """
    return get_info(db)["decks"]


@lru_cache(CACHE_SIZE)
def get_deck_names(db: sqlite3.Connection):
    """ Mapping of deck IDs (did) to deck names.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary mapping of deck id to deck name
    """
    dinfo = get_deck_info(db)
    return {
        did: dinfo[did]["name"]
        for did in dinfo
    }


@lru_cache(CACHE_SIZE)
def get_model_info(db: sqlite3.Connection):
    """ Get information about models.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Nested dictionary
    """
    return get_info(db)["models"]


@lru_cache(CACHE_SIZE)
def get_model_names(db: sqlite3.Connection):
    """ Mapping of model IDs (mid) to model names.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary mapping of model id to model name
    """
    minfo = get_model_info(db)
    return {
        mid: minfo[mid]["name"]
        for mid in minfo
    }


@lru_cache(CACHE_SIZE)
def get_field_names(db: sqlite3.Connection):
    """ Get names of the fields in the notes

    Args:
        db: Databse (:class:`sqlite3.Connection`)

    Returns:
        Dictionary mapping of model id to list of field names
    """
    minfo = get_model_info(db)
    return {
        mid: [
            flds["name"] for flds in minfo[mid]["flds"]
        ]
        for mid in minfo
    }


# Trivially derived setters
# ==============================================================================

def set_notes(db: sqlite3.Connection, df: pd.DataFrame, mode: str) -> None:
    """ Write notes table back into database.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: :class:`pandas.DataFrame`
        mode: 'update': Update only existing entries, 'append': Only append new
            entries, but do not modify, 'replace': Append, modify and delete

    Returns:
        None
    """
    _set_table(db, df, "notes", mode)


def set_cards(db: sqlite3.Connection, df: pd.DataFrame, mode: str):
    """ Write cards table back into database.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: :class:`pandas.DataFrame`
        mode: 'update': Update only existing entries, 'append': Only append new
            entries, but do not modify, 'replace': Append, modify and delete

    Returns:
        None
    """
    _set_table(db, df, "cards", mode)


def set_revs(db: sqlite3.Connection, df: pd.DataFrame, mode: str):
    """ Write review table back into database.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: :class:`pandas.DataFrame`
        mode: 'update': Update only existing entries, 'append': Only append new
            entries, but do not modify, 'replace': Append, modify and delete

    Returns:
        None
    """
    _set_table(db, df, "revs", mode)


# Merging information
# ==============================================================================

@lru_cache(CACHE_SIZE)
def cid2nid(db: sqlite3.Connection) -> dict:
    """ Mapping card ID to note ID.

    Args:
        db:  Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary
    """
    cards = get_table(db, "cards")
    return dict(zip(cards["id"].astype(str), cards["nid"].astype(str)))


@lru_cache(CACHE_SIZE)
def cid2did(db: sqlite3.Connection) -> dict:
    """ Mapping card ID to deck ID.

    Args:
        db:  Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary
    """
    cards = get_table(db, "cards")
    return dict(zip(cards["id"].astype(str), cards["did"].astype(str)))


@lru_cache(CACHE_SIZE)
def nid2mid(db: sqlite3.Connection) -> dict:
    """ Mapping note ID to model ID.

    Args:
        db:  Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary
    """
    notes = get_table(db, "notes")
    return dict(zip(notes["id"].astype(str), notes["mid"].astype(str)))


# fixme: This removes items whenever it can't merge!
# todo: move to util
# todo: id_add needs shouldn't have default
def merge_dfs(df: pd.DataFrame, df_add: pd.DataFrame, id_df: str,
              inplace=False, id_add="id", prepend="", replace=False,
              prepend_clash_only=True, columns=None,
              drop_columns=None):
    """
    Merge information from two dataframes.

    Args:
        df: Original :class:`pandas.DataFrame`
        df_add: :class:`pandas.DataFrame` to be merged with original
            :class:`pandas.DataFrame`
        id_df: Column of original dataframe that contains the id along which
            we merge.
        inplace: If False, return new dataframe, else update old one
        id_add: Column of the new dataframe that contains the id along which
            we merge
        prepend: Prepend a string to the column names from the new dataframe
        replace: Replace columns
        prepend_clash_only: Only prepend string to the column names from the
            new dataframe if there is a name clash.
        columns: Keep only these columns
        drop_columns: Drop these columns

    Returns:
        New merged :class:`pandas.DataFrame`
    """
    # Careful: Do not drop the id column until later (else we can't merge)
    # Still, we want to remove as much as possible here, because it's probably
    # better performing
    if columns:
        df_add = df_add.drop(
            set(df_add.columns)-(set(columns) | {id_add}), axis=1
        )
    if drop_columns:
        df_add = df_add.drop(set(drop_columns) - {id_add}, axis=1)
    # Careful: Rename columns after dropping unwanted ones
    if prepend_clash_only:
        col_clash = set(df.columns) & set(df_add.columns)
        rename_dict = {
            col: prepend + col for col in col_clash
        }
    else:
        rename_dict = {
            col: prepend + col for col in df_add.columns
        }
    df_add = df_add.rename(columns=rename_dict)
    # Careful: Might have renamed id_add as well
    if id_add in rename_dict:
        id_add = rename_dict[id_add]

    if replace:
        # Simply remove all potential clashes
        replaced_columns = set(df_add.columns).intersection(set(df.columns))
        df = df.drop(replaced_columns, axis=1)

    df_merge = df.merge(df_add, left_on=id_df, right_on=id_add)
    # Now remove id_add if it was to be removed
    # Careful: 'in' doesn't work with None
    if (columns and id_add not in columns) or \
            (drop_columns and id_add in drop_columns):
        df_merge.drop(id_add, axis=1, inplace=True)

    # todo: make optional
    # Make sure we don't have two ID columns
    new_id_add_col = id_add
    if id_add in rename_dict:
        new_id_add_col = rename_dict[id_add]
    if new_id_add_col in df_merge.columns and id_df != new_id_add_col:
        print("removing", new_id_add_col)
        df_merge.drop(new_id_add_col, axis=1, inplace=True)

    if inplace:
        return replace_df_inplace(df, df_merge)
    else:
        return df_merge
