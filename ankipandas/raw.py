#!/usr/bin/env python3

""" These function implement the more direct interactions with the Anki
database and provide basic functionality that is then used to implement the
functionality in :class:`~ankipandas.collection.Collection`,
:class:`ankipandas.ankidf.AnkiDataFrame` etc.

.. warning::

    Please only use these function if you know what you are doing, as they
    come with less consistency checks as the functionality implemented in
    :class:`~ankipandas.collection.Collection` and
    :class:`ankipandas.ankidf.AnkiDataFrame`.
    Also note that the functions here are considered to be internal, i.e. might
    change without prior notice.
"""

# std
from collections import defaultdict
import sqlite3
import json
import pathlib
from functools import lru_cache
from typing import Dict, List, Union

# 3rd
import pandas as pd
import numpy as np

# ours
from ankipandas.util.log import log
from ankipandas._columns import tables_ours2anki, anki_columns
from ankipandas.util.misc import nested_dict, defaultdict2dict

CACHE_SIZE = 32


# Open/Close db
# ==============================================================================


def load_db(path: Union[str, pathlib.PurePath]) -> sqlite3.Connection:
    """
    Load database from path.

    Args:
        path: String or :class:`pathlib.PurePath`.

    Returns:
        :class:`sqlite3.Connection`
    """
    path = pathlib.Path(path)
    if not path.is_file():
        raise FileNotFoundError("Not a file/file not found: {}".format(path))
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
        "SELECT * FROM {}".format(tables_ours2anki[table]), db
    )
    return df


def get_empty_table(table: str) -> pd.DataFrame:
    """ Get empty table

    Args:
        table: ``cards``, ``notes`` or ``revs``

    Returns:
        :class: `pandas.DataFrame`
    """
    return pd.DataFrame(columns=anki_columns[table])


def _interpret_json_val(val):
    if isinstance(val, str) and len(val) >= 1:
        try:
            return json.loads(val)
        except json.decoder.JSONDecodeError:
            return val
            # msg = (
            #     "AN ERROR OCCURRED WHILE TRYING TO LOAD INFORMATION "
            #     "FROM THE DATABASE. PLEASE COPY THE WHOLE INFORMATION"
            #     " BELOW AND ABOVE AND OPEN A BUG REPORT ON GITHUB!\n\n"
            # )
            # msg += "value to be parsed: {}".format(repr(val))
            # log.critical(msg)
            # raise
    else:
        return val


def read_info(db: sqlite3.Connection, table_name: str):
    """ Get a table from the database and return nested dictionary mapping of
    it.

    Args:
        db:
        table_name:

    Returns:

    """
    version = get_db_version(db)
    _df = pd.read_sql_query(
        "SELECT * FROM {table_name} ".format(table_name=table_name), db
    )
    if version == 0:
        assert len(_df) == 1, _df
        ret = {}
        for col in _df.columns:
            ret[col] = _interpret_json_val(_df[col][0])
    elif version == 1:
        ret = nested_dict()
        cols = _df.columns
        # todo: this is a hack, but oh well:
        index_cols = 1
        if len(_df[cols[0]].unique()) != len(_df):
            index_cols = 2
        for row in _df.iterrows():
            row = row[1].to_list()
            if index_cols == 1:
                for icol in range(1, len(cols)):
                    ret[row[0]][cols[icol]] = _interpret_json_val(row[icol])
            elif index_cols == 2:
                for icol in range(2, len(cols)):
                    ret[row[0]][row[1]][cols[icol]] = _interpret_json_val(
                        row[icol]
                    )
            else:
                raise ValueError
    else:
        raise NotImplementedError
    return defaultdict2dict(ret)


@lru_cache(CACHE_SIZE)
def get_info(db: sqlite3.Connection) -> dict:
    """
    Get all other information from the database, e.g. information about models,
    decks etc.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Nested dictionary.
    """
    return read_info(db, "col")


@lru_cache(CACHE_SIZE)
def get_db_version(db: sqlite3.Connection) -> int:
    """ Get "version" of database structure

    Args:
        db:

    Returns: 0: all info (also for decks and models) was in the 'col' table
        1: separate 'notetypes' and 'decks' tables

    """
    _tables = (
        db.cursor()
        .execute(
            "SELECT name FROM sqlite_master "
            "WHERE type ='table' AND name NOT LIKE 'sqlite_%';"
        )
        .fetchall()
    )
    tables = [ret[0] for ret in _tables]
    if "decks" in tables:
        return 1
    else:
        return 0


# Basic Setters
# ==============================================================================


def _consolidate_tables(
    df: pd.DataFrame, df_old: pd.DataFrame, mode: str, id_column="id"
):

    if not list(df.columns) == list(df_old.columns):
        raise ValueError(
            "Columns do not match: Old: {}, New: {}".format(
                ", ".join(df_old.columns), ", ".join(df.columns)
            )
        )

    old_indices = set(df_old[id_column])
    new_indices = set(df[id_column])

    # Get indices
    # -----------

    if mode == "update":
        indices = set(old_indices)
    elif mode == "append":
        indices = set(new_indices) - set(old_indices)
        if not indices:
            log.warning(
                "Was told to append to table, but there do not seem to be any"
                " new entries. "
            )
    elif mode == "replace":
        indices = set(new_indices)
    else:
        raise ValueError("Unknown mode '{}'.".format(mode))

    df = df[df[id_column].isin(indices)]

    # Apply
    # -----

    if mode == "update":
        df_new = df_old.copy()
        df_new.update(df)
    elif mode == "append":
        df_new = df_old.append(df, verify_integrity=True)
    elif mode == "replace":
        df_new = df.copy()
    else:
        raise ValueError("Unknown mode '{}'.".format(mode))

    return df_new


# fixme: update mode also can delete things if we do not have all rows
def set_table(
    db: sqlite3.Connection,
    df: pd.DataFrame,
    table: str,
    mode: str,
    id_column="id",
) -> None:
    """
    Write table back to database.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        df: The :class:`pandas.DataFrame` to write
        table: Table to write to: 'notes', 'cards', 'revs'
        mode: 'update': Update all existing entries, 'append': Only append new
            entries, but do not modify, 'replace': Append, modify and delete
        id_column: Column with ID
    Returns:
        None
    """
    df_old = get_table(db, table)
    df_new = _consolidate_tables(
        df=df, df_old=df_old, mode=mode, id_column=id_column
    )
    df_new.to_sql(tables_ours2anki[table], db, if_exists="replace", index=False)


class NumpyJSONEncoder(json.JSONEncoder):
    """ JSON Encoder that support numpy datatypes by converting them to
    built in datatypes. """

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NumpyJSONEncoder, self).default(obj)


def set_info(db: sqlite3.Connection, info: dict) -> None:
    """ Write back extra info to database

    Args:
        db: Database (:class:`sqlite3.Connection`)
        info: Output of :func:`get_info`

    Returns:
        None
    """

    def encode_value(value):
        if isinstance(value, (float, np.floating)):
            return value
        elif isinstance(value, (int, np.integer)):
            return value
        elif isinstance(value, str):
            return value
        else:
            return json.dumps(value, cls=NumpyJSONEncoder)

    info_json_strings = {
        key: encode_value(value) for key, value in info.items()
    }
    df = pd.DataFrame(info_json_strings, index=[0])
    df.to_sql("col", db, if_exists="replace", index=False)


# Trivially derived getters
# ==============================================================================

# todo: Using decorators here causes the function signatures to be messed up
#  with sphinx but oh well.


@lru_cache(CACHE_SIZE)
def get_ids(db: sqlite3.Connection, table: str) -> List[int]:
    """ Get list of IDs, e.g. note IDs etc.

    Args:
        db: Database (:class:`sqlite3.Connection`)
        table: 'revs', 'cards', 'notes'

    Returns:
        Nested dictionary
    """
    return get_table(db, table)["id"].astype(int).tolist()


@lru_cache(CACHE_SIZE)
def get_deck_info(db: sqlite3.Connection) -> dict:
    """ Get information about decks.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Nested dictionary
    """
    if get_db_version(db) == 0:
        _dinfo = get_info(db)["decks"]
    elif get_db_version(db) == 1:
        _dinfo = read_info(db, "decks")
    else:
        raise NotImplementedError

    if not _dinfo:
        return {}
    else:
        return _dinfo


@lru_cache(CACHE_SIZE)
def get_did2deck(db: sqlite3.Connection) -> Dict[int, str]:
    """ Mapping of deck IDs (did) to deck names.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary mapping
    """
    dinfo = get_deck_info(db)
    _did2dec = {int(did): dinfo[did]["name"] for did in dinfo}
    return defaultdict(str, _did2dec)


@lru_cache(CACHE_SIZE)
def get_deck2did(db: sqlite3.Connection) -> Dict[str, int]:
    """ Mapping of deck names to deck IDs

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary mapping of deck id to deck name
    """
    dinfo = get_deck_info(db)
    _did2dec = {dinfo[did]["name"]: int(did) for did in dinfo}
    return defaultdict(int, _did2dec)


@lru_cache(CACHE_SIZE)
def get_model_info(db: sqlite3.Connection) -> dict:
    """ Get information about models.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Nested dictionary
    """
    if get_db_version(db) == 0:
        _dinfo = get_info(db)["models"]
    elif get_db_version(db) == 1:
        _dinfo = read_info(db, "notetypes")
    else:
        raise NotImplementedError
    if not _dinfo:
        return {}
    else:
        return {int(key): value for key, value in _dinfo.items()}


@lru_cache(CACHE_SIZE)
def get_mid2model(db: sqlite3.Connection) -> Dict[int, str]:
    """ Mapping of model IDs (mid) to model names.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary mapping
    """
    minfo = get_model_info(db)
    _mid2model = {int(mid): minfo[mid]["name"] for mid in minfo}
    return defaultdict(str, _mid2model)


@lru_cache(CACHE_SIZE)
def get_model2mid(db: sqlite3.Connection) -> Dict[str, int]:
    """ Mapping of model name to model ID (mid)

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary mapping
    """
    minfo = get_model_info(db)
    _mid2model = {minfo[mid]["name"]: int(mid) for mid in minfo}
    return defaultdict(int, _mid2model)


@lru_cache(CACHE_SIZE)
def get_mid2sortfield(db: sqlite3.Connection) -> Dict[int, int]:
    """ Mapping of model ID to index of sort field. """
    if get_db_version(db) == 0:
        minfo = get_model_info(db)
        _mid2sortfield = {mid: minfo[mid]["sortf"] for mid in minfo}
        return defaultdict(int, _mid2sortfield)
    else:
        # fixme: Don't know how to retrieve sort field yet
        minfo = get_model_info(db)
        return {mid: 0 for mid in minfo}


@lru_cache(CACHE_SIZE)
def get_mid2fields(db: sqlite3.Connection) -> Dict[int, List[str]]:
    """ Get mapping of model ID to field names.

    Args:
        db: Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary mapping of model ID (mid) to list of field names.
    """
    if get_db_version(db) == 0:
        minfo = get_model_info(db)
        return {
            int(mid): [flds["name"] for flds in minfo[mid]["flds"]]
            for mid in minfo
        }
    elif get_db_version(db) == 1:
        finfo = read_info(db, "fields")
        mid2fields = {
            int(mid): [finfo[mid][ord]["name"] for ord in finfo[mid]]
            for mid in finfo
        }
        return mid2fields
    else:
        raise NotImplementedError


@lru_cache(CACHE_SIZE)
def get_mid2templateords(db: sqlite3.Connection) -> Dict[int, List[int]]:
    """ Get mapping of model ID to available templates ids

    Args:
        db:

    Returns:

    """
    if get_db_version(db) == 0:
        minfo = get_model_info(db)
        return {mid: [x["ord"] for x in minfo[mid]["tmpls"]] for mid in minfo}
    elif get_db_version(db) == 1:
        tinfo = read_info(db, "templates")
        return {int(mid): [int(x) for x in tinfo[mid]] for mid in tinfo}
    else:
        raise NotImplementedError


@lru_cache(CACHE_SIZE)
def get_cid2nid(db: sqlite3.Connection) -> Dict[int, int]:
    """ Mapping card ID to note ID.

    Args:
        db:  Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary
    """
    cards = get_table(db, "cards")
    _cid2nid = dict(zip(cards["id"], cards["nid"]))
    return defaultdict(int, _cid2nid)


@lru_cache(CACHE_SIZE)
def get_cid2did(db: sqlite3.Connection) -> Dict[int, int]:
    """ Mapping card ID to deck ID.

    Args:
        db:  Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary
    """
    cards = get_table(db, "cards")
    _cid2did = dict(zip(cards["id"], cards["did"]))
    return defaultdict(int, _cid2did)


@lru_cache(CACHE_SIZE)
def get_nid2mid(db: sqlite3.Connection) -> Dict[int, int]:
    """ Mapping note ID to model ID.

    Args:
        db:  Database (:class:`sqlite3.Connection`)

    Returns:
        Dictionary
    """
    notes = get_table(db, "notes")
    _nid2mid = dict(zip(notes["id"], notes["mid"]))
    return defaultdict(int, _nid2mid)
