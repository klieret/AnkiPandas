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

# todo: make public, doc
def _get_table(db: sqlite3.Connection, table: str) -> pd.DataFrame:
    df = pd.read_sql_query("SELECT * FROM {}".format(table), db)
    return df


def get_cards(db: sqlite3.Connection) -> pd.DataFrame:
    """
    Get all cards as a dataframe.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        :class:`pandas.DataFrame`
    """
    return _get_table(db, "cards")


def get_notes(db: sqlite3.Connection) -> pd.DataFrame:
    """
    Get all notes as a dataframe.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        :class:`pandas.DataFrame`
    """
    return _get_table(db, "notes")


def get_revlog(db: sqlite3.Connection) -> pd.DataFrame:
    """
    Get the revision log as a dataframe.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        :class:`pandas.DataFrame`
    """
    return _get_table(db, "revlog")


@lru_cache(cache_size)
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
    df_old = pd.read_sql_query("SELECT * FROM {}".format(table), db)
    old_indices = set(df_old[id_column])
    new_indices = set(df[id_column])
    if mode == "update":
        indices = set(old_indices)
    elif mode == "append":
        indices = set(new_indices) - set(old_indices)
        if not indices:
            # todo: logging
            return
    elif mode == "replace":
        indices = set(new_indices)
    else:
        raise ValueError("Unknown mode '{}'.".format(mode))
    # Remove everything not indices
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

@lru_cache(cache_size)
def get_deck_info(db: sqlite3.Connection):
    """ Get information about decks.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Nested dictionary
    """
    return get_info(db)["decks"]


@lru_cache(cache_size)
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


@lru_cache(cache_size)
def get_model_info(db: sqlite3.Connection):
    """ Get information about models.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Nested dictionary
    """
    return get_info(db)["models"]


@lru_cache(cache_size)
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


@lru_cache(cache_size)
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


def set_revlog(db: sqlite3.Connection, df: pd.DataFrame, mode: str):
    """ Write revlog table back into database.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: :class:`pandas.DataFrame`
        mode: 'update': Update only existing entries, 'append': Only append new
            entries, but do not modify, 'replace': Append, modify and delete

    Returns:
        None
    """
    _set_table(db, df, "revlog", mode)


# Merging information
# ==============================================================================
# todo: inplace passible decorator


# todo: move to utils
def _replace_df_inplace(df: pd.DataFrame, df_new: pd.DataFrame) -> None:
    """ Replace dataframe 'in place'.

    Args:
        df: :class:`pandas.DataFrame` to be replaced
        df_new: :class:`pandas.DataFrame` to replace the previous one

    Returns:
        None
    """
    if df.index.any():
        df.drop(df.index, inplace=True)
    for col in df_new.columns:
        df[col] = df_new[col]
    drop_cols = set(df.columns) - set(df_new.columns)
    if drop_cols:
        df.drop(drop_cols, axis=1, inplace=True)


def merge_dfs(df: pd.DataFrame, df_add: pd.DataFrame, id_df: str,
              inplace=False, id_add="id", prepend="",
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
    df_merge = df.merge(df_add, left_on=id_df, right_on=id_add)
    # Now remove id_add if it was to be removed
    # Careful: 'in' doesn't work with None
    if (columns and id_add not in columns) or \
            (drop_columns and id_add in drop_columns):
        df_merge.drop(id_add, axis=1, inplace=True)
    if inplace:
        _replace_df_inplace(df, df_merge)
    else:
        return df_merge


def merge_notes(db: sqlite3.Connection, df: pd.DataFrame,
                inplace=False, columns=None, drop_columns=None,
                nid_column="nid", prepend="n", prepend_clash_only=True):
    """ Merge note table into existing dataframe.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: :class:`pandas.DataFrame` to merge information into
        inplace: If False, return new dataframe, else update old one
        columns: Columns to merge
        drop_columns: Columns to ignore when merging
        nid_column: Column to match note id onto
        prepend: Prepend this string to fields from note table
        prepend_clash_only: Only prepend the ``prepend`` string when column
            names would otherwise clash.

    Returns:
        New :class:`pandas.DataFrame` if inplace==True, else None
    """
    return merge_dfs(
        df=df,
        df_add=get_notes(db),
        id_df=nid_column,
        id_add="nid",
        inplace=inplace,
        prepend=prepend,
        prepend_clash_only=prepend_clash_only,
        columns=columns,
        drop_columns=drop_columns
    )


def merge_cards(db: sqlite3.Connection, df: pd.DataFrame, inplace=False,
                columns=None, drop_columns=None,
                cid_column="cid", prepend="c", prepend_clash_only=True):
    """
    Merges information from the card table into the current dataframe.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: :class:`pandas.DataFrame` to merge information into
        inplace: If False, return new dataframe, else update old one
        columns:  Columns to merge
        drop_columns:  Columns to ignore when merging
        cid_column: Column to match card id onto
        prepend: Prepend this string to fields from card table
        prepend_clash_only: Only prepend the ``prepend`` string when column
            names would otherwise clash.

    Returns:
        New :class:`pandas.DataFrame` if inplace==True, else None
    """
    return merge_dfs(
        df=df,
        df_add=get_cards(db),
        id_df=cid_column,
        inplace=inplace,
        columns=columns,
        drop_columns=drop_columns,
        id_add="cid",
        prepend=prepend,
        prepend_clash_only=prepend_clash_only
    )


def add_nids(db: sqlite3.Connection, df: pd.DataFrame, inplace=False,
             cid_column="cid"):
    """ Add note IDs to a dataframe that only contains card ids.
    Example: ``add_nids(db, cards, id_column="nid")``

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: :class:`pandas.DataFrame` to merge information into
        inplace: If False, return new dataframe, else update old one
        cid_column: Column with card ID

    Returns:
        New :class:`pandas.DataFrame` if inplace==True, else None
    """
    if "nid" in df.columns:
        if inplace:
            return
        else:
            return df
    return merge_dfs(
        df=df,
        df_add=get_cards(db),
        id_df=cid_column,
        inplace=inplace,
        columns=["nid"],
        id_add="id",
        prepend="",
    )


def add_mids(db: sqlite3.Connection, df: pd.DataFrame, inplace=False,
             nid_column="nid"):
    """ Add model IDs to a dataframe that only contains note ids.

    Example: ``add_mids(db, notes, id_column="id")``,
    ``add_mids(db, cards_with_merged_notes, id_column="nid")``.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: :class:`pandas.DataFrame` to merge information into
        inplace: If False, return new dataframe, else update old one
        nid_column: Column with note ID

    Returns:
        New :class:`pandas.DataFrame` if inplace==True, else None
    """
    if "mid" in df.columns:
        if inplace:
            return
        else:
            return df
    return merge_dfs(
        df=df,
        df_add=get_notes(db),
        id_df=nid_column,
        inplace=inplace,
        columns=["mid"],
        id_add="nid",
        prepend="",
    )


# Predigesting information
# ==============================================================================

# Models
# ------------------------------------------------------------------------------

def add_mnames(db: sqlite3.Connection, df: pd.DataFrame, inplace=False,
               mid_column="mid", new_column="mname"):
    """ Add model names to a dataframe that contains model IDs.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: :class:`pandas.DataFrame` to merge information into
        inplace: If False, return new dataframe, else update old one
        mid_column: Column with model ID
        new_column: Name of new column to be added

    Returns:
        New :class:`pandas.DataFrame` if inplace==True, else None
    """
    if mid_column not in df.columns:
        raise ValueError(
            "Could not find model id column '{}'. You can specify a custom one "
            "using the mid_column option.".format(mid_column)
        )
    if inplace:
        df[new_column] = df[mid_column].astype(str).map(get_model_names(db))
    else:
        df = copy.deepcopy(df)
        add_mnames(db, df, inplace=True, mid_column=mid_column,
                   new_column=new_column)
        return df

# Cards
# ------------------------------------------------------------------------------


def add_dnames(db: sqlite3.Connection, df: pd.DataFrame, inplace=False,
               did_column="did", new_column="dname"):
    """
    Add deck names to a dataframe that contains deck IDs.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: :class:`pandas.DataFrame` to merge information into
        inplace: If False, return new dataframe, else update old one
        did_column: Column with deck ID (did)
        new_column: Name of new column to be added

    Returns:
        New :class:`pandas.DataFrame` if inplace==True, else None
    """
    if did_column not in df.columns:
        raise ValueError(
            "Could not find deck id column '{}'. You can specify a custom one "
            "using the did_column option.".format(did_column)
        )
    if inplace:
        df[new_column] = df[did_column].astype(str).map(get_deck_names(db))
    else:
        df = copy.deepcopy(df)
        add_dnames(db, df, did_column=did_column, new_column=new_column,
                   inplace=True)
        return df

# Notes
# ------------------------------------------------------------------------------


def add_fields_as_columns(db: sqlite3.Connection, df: pd.DataFrame,
                          inplace=False, mid_column="mid", prepend="",
                          flds_column="flds"):
    """
    In the 'notes' table, the field contents of the notes is contained in one
    column ('flds') by default. With this method, this column can be split up
    into a new column for every field.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: :class:`pandas.DataFrame` to merge information into
        inplace: If False, return new dataframe, else update old one
        mid_column: Column with model ID
        prepend: Prepend string to all new column names
        flds_column: Column that contains the joined fields

    Returns:
        New :class:`pandas.DataFrame` if inplace==True, else None
    """
    if mid_column not in df.columns:
        raise ValueError(
            "Could not find model id column '{}'. You can specify a custom one "
            "using the mid_column option.".format(mid_column)
        )
    if flds_column not in df.columns:
        raise ValueError(
            "Could not find fields column '{}'. You can specify a custom one "
            "using the flds_column option.".format(flds_column)
        )
    # fixme: What if one field column is one that is already in use?
    if inplace:
        mids = df["mid"].unique()
        for mid in mids:
            df_model = df[df[mid_column] == mid]
            fields = df_model[flds_column].str.split("\x1f", expand=True)
            for ifield, field in enumerate(get_field_names(db)[str(mid)]):
                df.loc[df[mid_column] == mid, prepend + field] = fields[ifield]
    else:
        df = copy.deepcopy(df)
        add_fields_as_columns(db, df, mid_column=mid_column, prepend=prepend,
                              inplace=True, flds_column=flds_column)
        return df


# fixme: what if fields aren't found?
def fields_as_columns_to_flds(db: sqlite3.Connection, df: pd.DataFrame,
                              inplace=False, mid_column="mid", prepended="",
                              drop=False):
    """
    This reverts :py:func:`~ankipandas.core_functions.add_fields_as_columns`,
    all columns that represented field contents are now merged into one column
    'flds'.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: :class:`pandas.DataFrame` to merge information into
        inplace: If False, return new dataframe, else update old one
        mid_column: Column with model ID
        prepended: Use this, if the name of columns that contained the fields
            had a string prepended to them
        drop: Drop columns that were now merged into the 'flds' column

    Returns:
        New :class:`pandas.DataFrame` if inplace==True, else None
    """
    if mid_column not in df.columns:
        raise ValueError(
            "Could not find model id column '{}'. You can specify a custom one "
            "using the mid_column option.".format(mid_column)
        )
    if inplace:
        mids = df[mid_column].unique()
        to_drop = []
        for mid in mids:
            fields = get_field_names(db)[str(mid)]
            if prepended:
                fields = [prepended + field for field in fields]
            df.loc[df[mid_column] == mid, "flds"] = \
                pd.Series(df[fields].values.tolist()).str.join("\x1f")
            if drop:
                # Careful: Do not delete the fields here yet, other models
                # might still use them
                to_drop.extend(fields)
        df.drop(to_drop, axis=1, inplace=True)
    else:
        df = copy.deepcopy(df)
        fields_as_columns_to_flds(
            db,
            df,
            inplace=True,
            mid_column=mid_column,
            prepended=prepended,
            drop=drop,
        )
        return df
