#!/usr/bin/env python3

# std
from pathlib import Path
import shutil
import tempfile
from typing import Optional, Dict

import ankipandas.paths
import ankipandas.raw as raw
from ankipandas.ankidf import AnkiDataFrame


class Collection(object):
    def __init__(self, path, user=None):
        path = ankipandas.paths.db_path_input(path, user=user)

        #: Path to currently loaded database
        self.path = path

        self._working_dir = tempfile.TemporaryDirectory()
        self._working_path = Path(self._working_dir.name) / "collection.anki2"
        shutil.copy2(str(self.path), str(self._working_path))

        #: Opened Anki database (:class:`sqlite3.Connection`)
        self.db = raw.load_db(self._working_path)

        #: Should be accessed with _get_item!
        self.__items = {
            "notes": None,
            "cards": None,
            "revs": None
        }  # type: Dict[str, AnkiDataFrame]

        #: Should be accessed with _get_original_item!
        self.__original_items = {
            "notes": None,
            "cards": None,
            "revs": None
        }  # type: Dict[str, AnkiDataFrame]


    def _get_original_item(self, item):
        r = self.__original_items[item]
        if r is None:
            if item in ["notes", "revs", "cards"]:
                r = AnkiDataFrame.init_with_table(self, item)
                self.__original_items[item] = r
        return r

    def _get_item(self, item):
        r = self.__items[item]
        if r is None:
            r = self._get_original_item(item)
            self.__items[item] = r
        return r

    @property
    def notes(self):
        return self._get_item("notes")

    @notes.setter
    def notes(self, value):
        self.__items["notes"] = value
    
    @property
    def cards(self):
        return self._get_item("cards")

    @cards.setter
    def cards(self, value):
        self.__items["cards"] = value
    
    @property
    def revs(self):
        return self._get_item("revs")

    @revs.setter
    def revs(self, value):
        self.__items["revs"] = value

    def __del__(self):
        if self._working_dir is not None:
            self._working_dir.cleanup()

    def empty_notes(self):
        return AnkiDataFrame.init_with_table(self, "notes", empty=True)

    def empty_cards(self):
        return AnkiDataFrame.init_with_table(self, "cards", empty=True)

    def empty_revs(self):
        return AnkiDataFrame.init_with_table(self, "revs", empty=True)

    def summarize_changes(self, output="print") -> Optional[Dict[str, dict]]:
        """ Summarize changes that were made with respect to the table
        as loaded from the database.
        If notes/cards/etc. were not loaded at all (and hence also definitely
        not modified), they do not appear in the output.

        Args:
            output: Output mode: 'print' (default: print)
                or 'dict' (return as dictionary of dictionaries of format
                ``{<type (cards/notes/...)>: {<key>: <value>}}``.

        Returns:
            None or dictionary of dictionaries
        """
        if output == "dict":
            as_dict = {}
            for key, value in self.__items.items():
                if value is not None:
                    as_dict[key] = value.summarize_changes(output="dict")
            return as_dict
        elif output == "print":
            for key, value in self.__items.items():
                if value is not None:
                    print("======== {} ========".format(key))
                    value.summarize_changes()
        else:
            raise ValueError("Invalid output setting: {}".format(output))
