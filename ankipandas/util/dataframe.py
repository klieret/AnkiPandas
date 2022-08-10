""" DataFrame utilities. """

# std
from __future__ import annotations

# 3rd
import pandas as pd

# ours
from ankipandas.util.log import log


def _sync_metadata(df_ret: pd.DataFrame, df_old: pd.DataFrame) -> None:
    """
    If the df_old has a `_metadata` field, containing a list of attribute
    names that contain metadata, then this is copied from `df_old` to the new
    dataframe `df_ret.

    Args:
        df_ret:
        df_old:

    Returns:
        None
    """
    if hasattr(df_old, "_metadata"):
        for key in df_old._metadata:
            value = getattr(df_old, key)
            log.debug("Setting metadata attribute %s to %s", key, value)
            setattr(df_ret, key, value)


def replace_df_inplace(df: pd.DataFrame, df_new: pd.DataFrame) -> None:
    """Replace dataframe 'in place'.
    If the dataframe has a `_metadata` field, containing a list of attribute
    names that contain metadata, then this is copied from `df` to the new
    dataframe.

    Args:
        df: :class:`pandas.DataFrame` to be replaced
        df_new: :class:`pandas.DataFrame` to replace the previous one

    Returns:
        None
    """
    # Drop all ROWs (not columns)
    if df.index.any():
        df.drop(df.index, inplace=True)
    for col in df_new.columns:
        df[col] = df_new[col]
    drop_cols = set(df.columns) - set(df_new.columns)
    if drop_cols:
        df.drop(drop_cols, axis=1, inplace=True)
    _sync_metadata(df_new, df)


# todo: this might be made more elegant in the future for sure...
# fixme: This removes items whenever it can't merge!
def merge_dfs(
    df: pd.DataFrame,
    df_add: pd.DataFrame,
    id_df: str,
    inplace=False,
    id_add="id",
    prepend="",
    replace=False,
    prepend_clash_only=True,
    columns=None,
    drop_columns=None,
) -> pd.DataFrame | None:
    """
    Merge information from two dataframes.
    If the dataframe has a `_metadata` field, containing a list of attribute
    names that contain metadata, then this is copied from `df` to the new
    dataframe.

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
            set(df_add.columns) - (set(columns) | {id_add}), axis=1
        )
    if drop_columns:
        df_add = df_add.drop(set(drop_columns) - {id_add}, axis=1)
    # Careful: Rename columns after dropping unwanted ones
    if prepend_clash_only:
        col_clash = set(df.columns) & set(df_add.columns)
        rename_dict = {col: prepend + col for col in col_clash}
    else:
        rename_dict = {col: prepend + col for col in df_add.columns}
    df_add = df_add.rename(columns=rename_dict)
    # Careful: Might have renamed id_add as well
    if id_add in rename_dict:
        id_add = rename_dict[id_add]

    if replace:
        # Simply remove all potential clashes
        replaced_columns = set(df_add.columns) & set(df.columns)
        df = df.drop(replaced_columns, axis=1)

    merge_kwargs = {}

    if id_add in df_add.columns:
        merge_kwargs["right_on"] = id_add
    elif id_add == df_add.index.name:
        merge_kwargs["right_index"] = True
    else:
        raise ValueError(f"'{id_add}' is neither index nor column.")

    if id_df in df.columns:
        merge_kwargs["left_on"] = id_df
    elif id_df == df.index.name:
        merge_kwargs["left_index"] = True
    else:
        raise ValueError(f"'{id_df}' is neither index nor column.")

    df_merge = df.merge(df_add, **merge_kwargs)

    # Now remove id_add if it was to be removed
    # Careful: 'in' doesn't work with None
    if (columns and id_add not in columns) or (
        drop_columns and id_add in drop_columns
    ):
        df_merge.drop(id_add, axis=1, inplace=True)

    # Make sure we don't have two ID columns
    new_id_add_col = id_add
    if id_add in rename_dict:
        new_id_add_col = rename_dict[id_add]
    if new_id_add_col in df_merge.columns and id_df != new_id_add_col:
        df_merge.drop(new_id_add_col, axis=1, inplace=True)

    _sync_metadata(df_merge, df)

    if inplace:
        replace_df_inplace(df, df_merge)
        return None  # mypy
    else:
        return df_merge
