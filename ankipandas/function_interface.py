#!/usr/bin/env python3

# ours
from ankipandas.ankipandas import AnkiPandas


# todo: automatically find database
def get_cards_df(
    path,
    deck_names=True,
    merge_notes=True,
    expand_fields=True
):
    """
    Return all cards as a pandas dataframe.

    Args:
        path: Path to database
        merge_notes: Merge information from the notes (default True), e.g. all
            of the fields.
        deck_names: Add a column "deck_names" in addition to the did (deck id)
            column (default True)
        expand_fields:
            When merging notes, epxand the 'flds' column to have a column for
            every field.
    Returns:
        Pandas dataframe
    """
    ap = AnkiPandas(path)
    return ap.cards(
        deck_names=deck_names,
        merge_notes=merge_notes,
        expand_fields=expand_fields
    )
