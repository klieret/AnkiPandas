#!/usr/bin/env python3

import ankipandas.paths
import ankipandas.raw as raw
from ankipandas.ankidf import AnkiDataFrame


class Collection(object):
    def __init__(self, path, user=None):
        path = ankipandas.paths.db_path_input(path, user=user)

        #: Path to currently loaded database
        self.path = path

        #: Opened Anki database (:class:`sqlite3.Connection`)
        self.db = raw.load_db(path)

    def notes(self, empty=False):
        return AnkiDataFrame.init_with_table(
            col=self,
            table="notes",
            empty=empty
        )

    def cards(self, empty=False):
        return AnkiDataFrame.init_with_table(
            col=self,
            table="cards",
            empty=empty
        )

    def revs(self, empty=False):
        return AnkiDataFrame.init_with_table(
            col=self,
            table="revs",
            empty=empty
        )