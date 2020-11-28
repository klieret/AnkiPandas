#!/usr/bin/env python3

# std
import copy
from pathlib import Path

# 3rd
import pandas as pd
import numpy as np

# todo: Docstrings, cleanup

# ours
from ankipandas.util.misc import invert_dict

tables_ours2anki = {"revs": "revlog", "cards": "cards", "notes": "notes"}
tables_anki2ours = invert_dict(tables_ours2anki)

fields_file = Path(__file__).parent / "data" / "anki_fields.csv"
fields_df = pd.read_csv(fields_file)

#: Maps table type to name of the index. E.g. the index of the notes is called
#: nid.
table2index = {"cards": "cid", "notes": "nid", "revs": "rid"}

our_tables = sorted(list(tables_ours2anki.keys()))
our_columns = {
    table: sorted(
        list(
            fields_df[(fields_df["Table"] == table) & fields_df["Default"]][
                "Column"
            ].unique()
        )
    )
    for table in our_tables
}
# Remove indices
for table, columns in our_columns.items():
    columns.remove(table2index[table])

# hard code this here, because order is important
anki_columns = {
    "cards": [
        "id",
        "nid",
        "did",
        "ord",
        "mod",
        "usn",
        "type",
        "queue",
        "due",
        "ivl",
        "factor",
        "reps",
        "lapses",
        "left",
        "odue",
        "odid",
        "flags",
        "data",
    ],
    "notes": [
        "id",
        "guid",
        "mid",
        "mod",
        "usn",
        "tags",
        "flds",
        "sfld",
        "csum",
        "flags",
        "data",
    ],
    "revs": [
        "id",
        "cid",
        "usn",
        "ease",
        "ivl",
        "lastIvl",
        "factor",
        "time",
        "type",
    ],
}

columns_ours2anki = {
    table: dict(
        zip(
            fields_df[(fields_df["Table"] == table) & fields_df["Native"]][
                "Column"
            ],
            fields_df[(fields_df["Table"] == table) & fields_df["Native"]][
                "AnkiColumn"
            ],
        )
    )
    for table in our_tables
}


columns_anki2ours = {
    table: invert_dict(columns_ours2anki[table]) for table in our_tables
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
            3: "in learning",
        },
        "ctype": {0: "learning", 1: "review", 2: "relearn", 3: "cram"},
    },
    "revs": {"rtype": {0: "learning", 1: "review", 2: "relearn", 3: "cram"}},
}

dtype_casts = {"notes": {}, "cards": {}, "revs": {}}

# todo: more precise?
dtype_casts_back = {"notes": {}, "cards": {}, "revs": {}}

# Avoiding problem with ints to floats such as here:
# https://github.com/pandas-dev/pandas/issues/4094
# Also be careful with platform dependent length of the int type, else this
# causes this error https://stackoverflow.com/questions/38314118/
# on Windows machines as stated by CalculusAce in
# https://github.com/klieret/AnkiPandas/issues/41
dtype_casts2 = {
    "cards": {
        "cord": np.int64,
        "cmod": np.int64,
        "cusn": np.int64,
        "cdue": np.int64,
        "civl": np.int64,
        "cfactor": np.int64,
        "creps": np.int64,
        "clapses": np.int64,
        "cleft": np.int64,
        "codue": np.int64,
    },
    "notes": {"nmod": np.int64, "nusn": np.int64},
    "revs": {
        "cid": np.int64,
        "rusn": np.int64,
        "rease": np.int64,
        "ivl": np.int64,
        "lastivl": np.int64,
        "rfactor": np.int64,
        "rtime": np.int64,
    },
}
dtype_casts_all = copy.deepcopy(dtype_casts2["cards"])
dtype_casts_all.update(dtype_casts2["notes"])
dtype_casts_all.update(dtype_casts2["revs"])
