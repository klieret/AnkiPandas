#!/usr/bin/env python3

# std
import sqlite3
import json
import pathlib
from functools import lru_cache
import copy

# 3rd
import pandas as pd


cache_size = 32


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


def close_db(db):
    """ Close the database. """
    db.close()


# Basic getters
# ==============================================================================

def get_cards(db):
    """
    Get all cards as a dataframe.

    Args:
        db: Database

    Returns:
        pandas.DataFrame
    """
    return pd.read_sql_query("SELECT * FROM cards ", db)


def get_notes(db):
    """
    Get all notes as a dataframe.

    Args:
        db: Database

    Returns:
        pandas.DataFrame
    """
    return pd.read_sql_query("SELECT * FROM notes ", db)


def get_revlog(db):
    """
    Get the revision log as a dataframe.

    Args:
        db: Database

    Returns:
        pandas.DataFrame
    """
    return pd.read_sql_query("SELECT * FROM revlog ", db)


@lru_cache(cache_size)
def get_info(db):
    """
    Get all other information from the databse, e.g. information about models,
    decks etc.

    Args:
        db: Databse

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


# Trivially derived getters
# ==============================================================================


@lru_cache(cache_size)
def get_deck_info(db):
    return get_info(db)["decks"]


@lru_cache(cache_size)
def get_deck_names(db):
    dinfo = get_deck_info(db)
    return {
        did: dinfo[did]["name"]
        for did in dinfo
    }


@lru_cache(cache_size)
def get_model_info(db):
    return get_info(db)["models"]


@lru_cache(cache_size)
def get_model_names(db):
    minfo = get_model_info(db)
    return {
        mid: minfo[mid]["name"]
        for mid in minfo
    }


@lru_cache(cache_size)
def get_field_names(db):
    minfo = get_model_info(db)
    return {
        mid: [
            flds["name"] for flds in minfo[mid]["flds"]
        ]
        for mid in minfo
    }


# Merging information
# ==============================================================================
# todo: inplace passible decorator


def _replace_inplace(df, df_new):
    df.drop(df.index, inplace=True)
    for col in df_new.columns:
        df[col] = df_new[col]


def merge_dfs(df, df_add, id_df, inplace=False, id_add="id", prepend="",
              prepend_clash_only=True, columns=None, drop_columns=None):
    """
    Merge information from two dataframes

    Args:
        df: Original dataframe
        df_add: Dataframe to be merged with original dataframe
        id_df: Column of original dataframe that contains the id along which
            we merge.
        inplace: If False, return new dataframe, else update old one
        id_add: Column of the new dataframe that contains the id along which
            we merge
        prepend: Prepend a string to the column names from the new dataframe
        prepend_clash_only: Only prepend string to the column names from the
            new dataframe if there is a name clash.
        columns: Keep only these columns
        drop_columns: Drop these columns

    Returns:
        New merged dataframe
    """
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
    if columns:
        df_add.drop(set(df_add.columns)-set(columns), axis=1, inplace=True)
    if drop_columns:
        df_add.drop(drop_columns, axis=1, inplace=True)
    df_merge = df.merge(df_add, left_on=id_df, right_on=id_add)
    if inplace:
        _replace_inplace(df, df_merge)
    else:
        return df_merge


def merge_note_info(db, df, inplace=False, columns=None, drop_columns=None,
                    id_column="nid", prepend="n", prepend_clash_only=True):
    return merge_dfs(
        df=df,
        df_add=get_notes(db),
        id_df=id_column,
        id_add="nid",
        inplace=inplace,
        prepend=prepend,
        prepend_clash_only=prepend_clash_only,
        columns=columns,
        drop_columns=drop_columns
    )


def merge_card_info(db, df, inplace=False, columns=None, drop_columns=None,
                    id_column="cid", prepend="c", prepend_clash_only=True):
    return merge_dfs(
        df=df,
        df_add=get_cards(db),
        id_df=id_column,
        inplace=inplace,
        columns=columns,
        drop_columns=drop_columns,
        id_add="cid",
        prepend=prepend,
        prepend_clash_only=prepend_clash_only
    )


def add_nids(db, df, inplace=False, id_column="cid"):
    """ Add note IDs to a dataframe that only contains card ids. """
    return merge_dfs(
        df=df,
        df_add=get_cards(db),
        id_df=id_column,
        inplace=inplace,
        columns=["nid"],
        id_add="id",
        prepend="",
    )


def add_mids(db, df, inplace=False, id_column="cid"):
    """ Add note IDs to a dataframe that only contains card ids. """
    return merge_dfs(
        df=df,
        df_add=get_notes(db),
        id_df=id_column,
        inplace=inplace,
        columns=["mid"],
        id_add="nid",
        prepend="",
    )


# Predigesting information
# ==============================================================================

# Models
# ------------------------------------------------------------------------------

def add_model_names(db, df, inplace=False, id_column="mid", new_column="mname"):
    if not id_column in df.columns:
        raise ValueError(
            "Could not find id column '{}'. You can specify a custom one using"
            " the id_column option.".format(id_column)
        )
    if inplace:
        df[new_column] = df[id_column].map(get_model_names(db))
    else:
        df = copy.deepcopy(df)
        add_model_names(db, df, inplace=True)
        return df

# Cards
# ------------------------------------------------------------------------------


def add_deck_names(db, df, inplace=False, id_column="did", new_column="dname"):
    if not id_column in df.columns:
        raise ValueError(
            "Could not find id column '{}'. You can specify a custom one using"
            " the id_column option.".format(id_column)
        )
    if inplace:
        df[new_column] = df[id_column].map(get_deck_names(db))
    else:
        df = copy.deepcopy(df)
        add_model_names(db, df, id_column=id_column, new_column=new_column,
                        inplace=True)
        return df

# Notes
# ------------------------------------------------------------------------------


def add_fields_as_columns(db, df, inplace=False, id_column="mid", prepend=""):
    if not id_column in df.columns:
        raise ValueError(
            "Could not find id column '{}'. You can specify a custom one using"
            " the id_column option.".format(id_column)
        )
    mids = df["mid"].unique()
    if inplace:
        for mid in mids:
            df_model = df[df["mid"] == mid]
            fields = df_model["flds"].str.split("\x1f", expand=True)
            for ifield, field in enumerate(get_field_names(db)[str(mid)]):
                df.loc[df["mid"] == mid, prepend + field] = fields[ifield]
    else:
        df = copy.deepcopy(df)
        add_fields_as_columns(db, df, id_column=id_column, prepend=prepend,
                              inplace=True)
        return df
