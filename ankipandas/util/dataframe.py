#!/usr/bin/env python3

""" DataFrame utilities. """

# 3rd
import pandas as pd


def replace_df_inplace(df: pd.DataFrame, df_new: pd.DataFrame) -> None:
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
