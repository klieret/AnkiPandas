#!/usr/bin/env python3

# todo: move this file out of data

# ours
from ankipandas.util.misc import invert_dict

# todo: add other tables
tables_ours2anki = {
    "revs": "revlog",
    "cards": "cards",
    "notes": "notes"
}
tables_anki2ours = invert_dict(tables_ours2anki)

# format: our type: original type
columns_ours2anki = {
    "cards": {
        'cid': 'id',
        'nid': 'nid',
        'did': 'did',
        'cord': 'ord',
        'cmod': 'mod',
        'cusn': 'usn',
        'ctype': 'type',
        'cqueue': 'queue',
        'cdue': 'due',
        'civl': 'ivl',
        'cfactor': 'factor',
        'creps': 'reps',
        'clapses': 'lapses',
        'cleft': 'left',
        'codue': 'odue',
        'codid': 'odid',
        'cflags': 'flags',
        'cdata': 'data'
    },
    "notes": {
        'nid': 'id',
        'nguid': 'guid',
        'mid': 'mid',
        'nmod': 'mod',
        'nusn': 'usn',
        'ntags': 'tags',
        'nflds': 'flds',
        'nsfld': 'sfld',
        'ncsum': 'csum',
        'nflags': 'flags',
        'ndata': 'data',
    },
    "revs": {
        'rid': 'id',
        'cid': 'cid',
        'rusn': 'usn',
        'rease': 'ease',
        'rivl': 'ivl',
        'rlastIvl': 'lastIvl',
        'rfactor': 'factor',
        'rtime': 'time',
        'rtype': 'type'
    }
}
columns_anki2ours = {
    table: invert_dict(columns_ours2anki[table])
    for table in columns_ours2anki
}

our_columns = {
    table: sorted(list(columns_ours2anki[table].keys()))
    for table in columns_ours2anki
}
