#!/usr/bin/env python3

# std
from pathlib import Path, PurePath
import sqlite3
from typing import Optional, Dict, Union, Any
import time

# ours
import ankipandas.paths
import ankipandas.raw as raw
from ankipandas.ankidf import AnkiDataFrame
from ankipandas.util.log import log


class Collection(object):
    def __init__(self, path=None, user=None):
        """ Initialize :class:`~ankipandas.collection.Collection` object.

        Args:
            path: (Search) path to database. See
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

        log.info("Loaded db from {}".format(self.path))

        #: Opened Anki database (:class:`sqlite3.Connection`)
        self.db = raw.load_db(self.path)  # type: sqlite3.Connection

        #: Should be accessed with _get_item!
        self.__items = {
            "notes": None,
            "cards": None,
            "revs": None,
        }  # type: Dict[str, AnkiDataFrame]

        #: Should be accessed with _get_original_item!
        self.__original_items = {
            "notes": None,
            "cards": None,
            "revs": None,
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

    def _prepare_write_data(
        self, modify=False, add=False, delete=False
    ) -> Dict[str, Any]:
        prepared = {}
        for key, value in self.__items.items():
            if value is None:
                log.debug("Write: Skipping {}, because it's None.".format(key))
                continue
            if key in ["notes", "cards", "revs"]:
                if not delete:
                    ndeleted = len(value.was_deleted())
                    if ndeleted:
                        raise ValueError(
                            "You specified delete=False, but {} rows of item "
                            "{} would be deleted.".format(ndeleted, key)
                        )
                if not modify:
                    nmodified = sum(value.was_modified(na=False))
                    if nmodified:
                        raise ValueError(
                            "You specified modify=False, but {} rows of item "
                            "{} would be modified.".format(nmodified, key)
                        )
                if not add:
                    nadded = sum(value.was_added())
                    if nadded:
                        raise ValueError(
                            "You specified add=False, but {} rows of item "
                            "{} would be modified.".format(nadded, key)
                        )

                mode = "replace"
                if modify and not add and not delete:
                    mode = "update"
                if add and not modify and not delete:
                    mode = "append"
                value._check_table_integrity()
                raw_table = value.raw()
                prepared[key] = {"raw": raw_table, "mode": mode}

        return prepared

    def _get_and_update_info(self) -> Dict[str, Any]:
        info = raw.get_info(self.db)
        info["mod"] = int(time.time() * 1000)  # Modification time stamp
        info["usn"] = -1  # Signals update needed
        if self.__items["notes"] is not None:
            missing_tags = list(
                set(info["tags"].keys())
                - set(self.__items["notes"].list_tags())
            )
            for tag in missing_tags:
                # I'm assuming that this is the usn (update sequence number)
                # of the tags
                info["tags"][tag] = -1
        return info

    def write(
        self,
        modify=False,
        add=False,
        delete=False,
        backup_folder: Union[PurePath, str] = None,
    ):
        """ Creates a backup of the database and then writes back the new
        data.

        .. danger::

            The switches ``modify``, ``add`` and ``delete`` will run additional
            cross-checks, but do not rely on them to 100%!

        .. warning::

            It is recommended to run :meth:`summarize_changes` before to check
            whether the changes match your expectation.

        .. note::

            Please make sure to thoroughly check your collection in Anki after
            every write process!

        Args:
            modify: Allow modification of existing items (notes, cards, etc.)
            add: Allow adding of new items (notes, cards, etc.)
            delete: Allow deletion of items (notes, cards, etc.)
            backup_folder: Path to backup folder. If None is given, the backup
                is created in the Anki backup directory (if found).

        Returns:
            None
        """
        if not modify and not add and not delete:
            log.warning(
                "Please set modify=True, add=True or delete=True, you're"
                " literally not allowing me any modification at all."
            )
            return None

        try:
            prepared = self._prepare_write_data(
                modify=modify, add=add, delete=delete
            )

            info = self._get_and_update_info()
        except Exception as e:
            log.critical(
                "Something went wrong preparing the data for writing. "
                "However, no data has been written out, so your"
                "database is save!"
            )
            raise e
        else:
            log.debug("Successfully prepared data for writing.")

        backup_path = ankipandas.paths.backup_db(
            self.path, backup_folder=backup_folder
        )
        log.info("Backup created at {}.".format(backup_path.resolve()))

        # Actually setting values here, after all conversion tasks have been
        # carried out. That way if any of them fails, we don't have a
        # partially written collection.
        log.debug("Now actually writing to database.")
        try:
            for table, values in prepared.items():
                raw.set_table(
                    self.db, values["raw"], table=table, mode=values["mode"]
                )
            # Actually only needed if we actually modify the info.
            # This will trigger a complete re-upload, so we want to avoid this
            # if possible.
            # raw.set_info(self.db, info)
        except Exception as e:
            log.critical(
                "Error while writing data to database at {path}"
                "This means that your database might have become corrupted. "
                "It's STRONGLY adviced that you manually restore the database "
                "by replacing it with the backup from {backup_path} and restart"
                " from scratch. "
                "Please also open a bug report at "
                "https://github.com/klieret/AnkiPandas/issues/, as errors "
                "during the actual writing process should never occurr!".format(
                    path=self.path.resolve(), backup_path=backup_path.resolve()
                )
            )
            raise e
