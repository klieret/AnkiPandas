#!/usr/bin/env python3

# std
from pathlib import Path
from typing import Optional, Dict
import sqlite3

# ours
import ankipandas.paths
import ankipandas.raw as raw
from ankipandas.ankidf import AnkiDataFrame


class Collection(object):
    def __init__(self, path, user=None):
        """ Initialize :class:`~ankipandas.collection.Collection` object.

        Args:
            path: (Search) path to database see
                :py:func:`~ankipandas.paths.db_path_input` for more
                information.
            user: Anki user name. See
                :py:func:`~ankipandas.paths.db_path_input` for more
                information.

        Examples:

        .. code-block:: python

            from ankipandas import Collection

            # Let ankipandas find the db for you
            col = Collection()

            # Let ankipandas find the db for this user (important if you have
            # more than one user account in Anki)
            col = Collection(user="User 1")

            # Specify full path to Anki's database
            col = Collection("/full/path/to/collection.anki2")

            # Speficy partial path to Anki's database and specify user
            col = Collection("/partial/path/to/collection", user="User 1")

        """
        path = ankipandas.paths.db_path_input(path, user=user)

        #: Path to currently loaded database
        self.path = path  # type: Path

        #: Opened Anki database (:class:`sqlite3.Connection`)
        self.db = raw.load_db(self.path)  # type: sqlite3.Connection

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
            r = self._get_original_item(item).copy(True)
            self.__items[item] = r
        return r

    @property
    def notes(self) -> AnkiDataFrame:
        """ Notes as :class:`ankipandas.ankidf.AnkiDataFrame`. """
        return self._get_item("notes")

    @notes.setter
    def notes(self, value):
        self.__items["notes"] = value
    
    @property
    def cards(self) -> AnkiDataFrame:
        """ Cards as :class:`ankipandas.ankidf.AnkiDataFrame`. """
        return self._get_item("cards")

    @cards.setter
    def cards(self, value):
        self.__items["cards"] = value
    
    @property
    def revs(self) -> AnkiDataFrame:
        """ Reviews as :class:`ankipandas.ankidf.AnkiDataFrame`. """
        return self._get_item("revs")

    @revs.setter
    def revs(self, value):
        self.__items["revs"] = value

    def empty_notes(self):
        """ Similar :class:`ankipandas.ankidf.AnkiDataFrame`
        to :attr:`notes`, but without any rows. """
        return AnkiDataFrame.init_with_table(self, "notes", empty=True)

    def empty_cards(self):
        """ Similar :class:`ankipandas.ankidf.AnkiDataFrame`
        to :attr:`cards`, but without any rows. """
        return AnkiDataFrame.init_with_table(self, "cards", empty=True)

    def empty_revs(self):
        """ Similar :class:`ankipandas.ankidf.AnkiDataFrame`
        to :attr:`revs`, but without any rows. """
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
