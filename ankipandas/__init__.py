#!/usr/bin/env python3

# std
import sys

# ours
import ankipandas.raw
import ankipandas.paths
import ankipandas.util
import ankipandas.paths
import ankipandas.collection
from ankipandas.collection import Collection
from ankipandas.paths import find_db, db_path_input
from ankipandas.ankidf import AnkiDataFrame
from ankipandas.util.log import log, set_log_level, set_debug_log_level


if sys.version_info < (3, 6):
    log.warning(
        "Your python version %s has reached its end of life. For more"
        " information on the life time of different python versions, see "
        "https://endoflife.date/python. Using python versions after their "
        "end of life can be dangerous (you will not receive security "
        "updates). Keeping old versions supported is also difficult for "
        "developers, so AnkiPandas has decided to drop support of python "
        " < 3.6. We strongly encourage you to update your python version to "
        "receive updates.",
        ".".join(map(str, sys.version_info)),
    )
