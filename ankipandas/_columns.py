#!/usr/bin/env python3

# std
from pathlib import Path

# 3rd
import pandas as pd
import numpy as np

# ours
from ankipandas.util.misc import invert_dict

tables_ours2anki = {
    "revs": "revlog",
    "cards": "cards",
    "notes": "notes"
}
tables_anki2ours = invert_dict(tables_ours2anki)

fields_file = Path(__file__).parent / "data" / "anki_fields.csv"
fields_df = pd.read_csv(fields_file)

table2index = {
    "cards": "cid",
    "notes": "nid",
    "revs": "rid"
}

our_tables = sorted(list(tables_ours2anki.keys()))
our_columns = {
    table: sorted(list(
        fields_df[np.logical_and(
            fields_df["Table"] == table,
            fields_df["Default"] == True
        )]["Column"].unique()
    ))
    for table in our_tables
}
# Remove indices
for table, columns in our_columns.items():
    columns.remove(table2index[table])

# hard code this here, because order is important
anki_columns = {
    "cards": [
        'id',
        'nid',
        'did',
        'ord',
        'mod',
        'usn',
        'type',
        'queue',
        'due',
        'ivl',
        'factor',
        'reps',
        'lapses',
        'left',
        'odue',
        'odid',
        'flags',
        'data'
    ],
    "notes": [
        'id',
        'guid',
        'mid',
        'mod',
        'usn',
        'tags',
        'flds',
        'sfld',
        'csum',
        'flags',
        'data',
    ],
    "revs": [
        'id',
        'cid',
        'usn',
        'ease',
        'ivl',
        'lastIvl',
        'factor',
        'time',
        'type'
    ]
}

columns_ours2anki = {
    table: dict(zip(
        fields_df[np.logical_and(fields_df["Table"] == table, fields_df["Native"] == True)]["Column"],
        fields_df[np.logical_and(fields_df["Table"] == table, fields_df["Native"] == True)]["AnkiColumn"]
    ))
    for table in our_tables
}


columns_anki2ours = {
    table: invert_dict(columns_ours2anki[table])
    for table in our_tables
}

value_maps = {
    "cards": {
        "cqueue": {
            -3: "sched buried",
            -2: "user buried",
            -1: "suspended",
            0: "new",
            1: "learning",
            2: "due",
            3: "in learning"
        },
        "ctype": {
            0: "learning",
            1: "review",
            2: "relearn",
            3: "cram"
        }
    },
    "revs": {
        "rtype": {
            0: "learning",
            1: "review",
            2: "relearn",
            3: "cram"
        }
    }
}

dtype_casts = {
    "notes": {"id": str, "mid": str},
    "cards": {"id": str, "nid": str, "did": str, "odid": str},
    "revs": {"id": str, "cid": str}
}

# todo: more precise?
dtype_casts_back = {
    "notes": {"id": int, "mid": int},
    "cards": {"id": int, "nid": int, "did": int, "odid": int},
    "revs": {"id": int, "cid": int}
}

# Avoiding problem with ints to floats such as here:
# https://github.com/pandas-dev/pandas/issues/4094
dtype_casts2 = {
    "cards": {
        "cord": int,
        "cmod": int,
        "cusn": int,
        "cdue": int,
        "civl": int,
        "cfactor": int,
        "creps": int,
        "clapses": int,
        "clef": int,
        "codue": int,
        "codid": int,
    },
    "notes": {
        "nmod": int,
        "nusn": int
    },
    "revs": {
        "cid": int,
        "rusn": int,
        "rease": int,
        "ivl": int,
        "lastivl": int,
        "rfactor": int,
        "rtime": int,
    }
}
