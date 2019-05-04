#!/usr/bin/env python3

_columns = {
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
    "revlog": [
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

columns = {
    table: sorted(_columns[table]) for table in _columns
}
