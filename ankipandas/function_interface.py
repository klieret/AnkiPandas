#!/usr/bin/env python3

# std
import os
import pathlib
import pandas as pd

# ours
import ankipandas.ankipandas as apd


def load_notes(
    path,
    expand_fields=True
):
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
):
    """
    Return all cards as a pandas dataframe.

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


def load_revs(
    path,
    merge_cards=True,
    merge_notes=True,
    expand_fields=True
):
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


def _find_anki_path(start_path=None):
    raise NotImplementedError


def _find_users(anki_path: pathlib.Path, user=None,
                collection_filename="collection.anki2"):
    if user:
        potential_users = [user]
    else:
        potential_users = [
            f.name for f in os.scandir(str(anki_path)) if f.is_dir()
        ]
    users = []
    for potential_user in potential_users:
        p = anki_path / potential_user / collection_filename
        if p.is_file():
            users.append(potential_user)
    return users


def find_database(basepath=None, user=None, search_home=True,
                  collection_filename="collection.anki2"):
    """
    
    Args:
        basepath:
        user: 
        search_home: 
        collection_filename: 

    Returns:

    """
    anki_paths = [
        "~/.local/share/Anki2/",
        "~/Documents/Anki2",
        "~/Anki2/"
    ]
    if basepath:
        anki_paths.insert(0, basepath)
    anki_paths = [pathlib.Path(p).expanduser() for p in anki_paths]
    anki_path = None
    for path in anki_paths:
        if not path.is_dir():
            continue
        anki_path = path
        break
    else:
        # Not found
        if search_home:
            anki_path = _find_anki_path()
    if not anki_path:
        raise RuntimeError("Could not find database.")

    if user:
        users = [user]
    else:
        users = _find_users(anki_path, collection_filename=collection_filename)
    if len(users) == 0:
        raise RuntimeError(
            "No database found in anki directory {}".format(anki_path)
        )
    if len(users) >= 2:
        raise RuntimeError(
            "More than one user account found in anki directory {}: {} "
            "Please select one with the 'user' keyword.".format(
                anki_path,
                ", ".join(users)
            )
        )

    # Everything good
    return anki_path / users[0] / collection_filename


def table_help():
    """
    Return a pandas dataframe containing descriptions of every field in the
    anki database.

    """
    # Display help text on column
    help_path = pathlib.Path(__file__).parent / "anki_fields.csv"
    df = pd.read_csv(help_path)
    return df
    # fields = df["Name"].unique()
    # if field:
    #     if field not in fields:
    #         print("Field '{}' does not exist.".format(field))
    #         df = pd.DataFrame()
    #     else:
    #         df = df[df["Name"] == field]
    # tables = [string.split(",") for string in df["Tables"].unique()]
    # if table:
    #     if table not in tables:
    #         print("Table '{}' does not exist.".format(table))
    #         df = pd.DataFrame()
    #     else:
    #         df = df[df["Tables"].str.contains(table)]
    # return df
