# std
from __future__ import annotations

import sqlite3
import time
from contextlib import closing
from pathlib import Path, PurePath
from typing import Any

# ours
import ankipandas.paths
import ankipandas.raw as raw
from ankipandas.ankidf import AnkiDataFrame
from ankipandas.util.log import log


class Collection:
    def __init__(self, path=None, user=None):
        """Initialize :class:`~ankipandas.collection.Collection` object.

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

            # Specify partial path to Anki's database and specify user
            col = Collection("/partial/path/to/collection", user="User 1")

        """
        path = ankipandas.paths.db_path_input(path, user=user)

        #: Path to currently loaded database
        self._path: Path = path

        #: Should be accessed with _get_item!
        self.__items: dict[str, AnkiDataFrame | None] = {
            "notes": None,
            "cards": None,
            "revs": None,
        }

        #: Should be accessed with _get_original_item!
        self.__original_items: dict[str, AnkiDataFrame | None] = {
            "notes": None,
            "cards": None,
            "revs": None,
        }

    @property
    def path(self) -> Path:
        """Path to currently loaded database"""
        return self._path

    @property
    def db(self) -> sqlite3.Connection:
        """Opened Anki database. Make sure to call `db.close()` after you're
        done. Better still, use `contextlib.closing`.
        """
        log.debug(f"Opening Db from {self._path}")
        return raw.load_db(self._path)

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
        """Notes as :class:`ankipandas.ankidf.AnkiDataFrame`."""
        return self._get_item("notes")

    @notes.setter
    def notes(self, value):
        self.__items["notes"] = value

    @property
    def cards(self) -> AnkiDataFrame:
        """Cards as :class:`ankipandas.ankidf.AnkiDataFrame`."""
        return self._get_item("cards")

    @cards.setter
    def cards(self, value):
        self.__items["cards"] = value

    @property
    def revs(self) -> AnkiDataFrame:
        """Reviews as :class:`ankipandas.ankidf.AnkiDataFrame`."""
        return self._get_item("revs")

    @revs.setter
    def revs(self, value):
        self.__items["revs"] = value

    def empty_notes(self):
        """Similar :class:`ankipandas.ankidf.AnkiDataFrame`
        to :attr:`notes`, but without any rows."""
        return AnkiDataFrame.init_with_table(self, "notes", empty=True)

    def empty_cards(self):
        """Similar :class:`ankipandas.ankidf.AnkiDataFrame`
        to :attr:`cards`, but without any rows."""
        return AnkiDataFrame.init_with_table(self, "cards", empty=True)

    def empty_revs(self):
        """Similar :class:`ankipandas.ankidf.AnkiDataFrame`
        to :attr:`revs`, but without any rows."""
        return AnkiDataFrame.init_with_table(self, "revs", empty=True)

    def summarize_changes(self, output="print") -> dict[str, dict] | None:
        """Summarize changes that were made with respect to the table
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
                    changes = value.summarize_changes(output="dict")
                    as_dict[key] = changes  # type: ignore
            return as_dict  # type: ignore
        elif output == "print":
            for key, value in self.__items.items():
                if value is not None:
                    print(f"======== {key} ========")
                    value.summarize_changes()
            return None  # explicit for mypy
        else:
            raise ValueError(f"Invalid output setting: {output}")

    def _prepare_write_data(
        self, modify=False, add=False, delete=False
    ) -> dict[str, Any]:
        prepared = {}
        for key, value in self.__items.items():
            if value is None:
                log.debug("Write: Skipping %s, because it's None.", key)
                continue
            if key in ["notes", "cards", "revs"]:
                ndeleted = len(value.was_deleted())
                nmodified = sum(value.was_modified(na=False))
                nadded = sum(value.was_added())

                if not delete and ndeleted:
                    raise ValueError(
                        "You specified delete=False, but {} rows of item "
                        "{} would be deleted.".format(ndeleted, key)
                    )
                if not modify and nmodified:
                    raise ValueError(
                        "You specified modify=False, but {} rows of item "
                        "{} would be modified.".format(nmodified, key)
                    )
                if not add and nadded:
                    raise ValueError(
                        "You specified add=False, but {} rows of item "
                        "{} would be modified.".format(nadded, key)
                    )

                if not ndeleted and not nmodified and not nadded:
                    log.debug(
                        "Skipping table %s for writing, because nothing "
                        "seemed to have changed",
                        key,
                    )
                    continue

                mode = "replace"
                if modify and not add and not delete:
                    mode = "update"
                if add and not modify and not delete:
                    mode = "append"
                log.debug("Will update table %s with mode %s", key, mode)
                value.check_table_integrity()
                raw_table = value.raw()
                prepared[key] = {"raw": raw_table, "mode": mode}

        return prepared

    def _get_and_update_info(self) -> dict[str, Any]:
        with closing(self.db) as db:
            info = raw.get_info(db)

            info_updates = dict(
                mod=int(time.time() * 1000),  # Modification time stamp
                usn=-1,  # Signals update needed
            )
            if raw.get_db_version(db) == 0:
                for key in info_updates:
                    assert key in info
                info.update(info_updates)
            elif raw.get_db_version(db) == 1:
                assert len(info) == 1
                first_key = list(info)[0]
                info[first_key].update(info_updates)
            # fixme: this currently doesn't work. In the new db structure there's
            #   a tags table instead of a field, but it doesn't seem to be
            #   used.
            # if self.__items["notes"] is not None:
            #
            #     missing_tags = list(
            #         set(info["tags"].keys())
            #         - set(self.__items["notes"].list_tags())
            #     )
            #     for tag in missing_tags:
            #         # I'm assuming that this is the usn (update sequence number)
            #         # of the tags
            #         info["tags"][tag] = -1
        return info

    def write(
        self,
        modify=False,
        add=False,
        delete=False,
        backup_folder: PurePath | str | None = None,
    ):
        """Creates a backup of the database and then writes back the new
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
            log.debug("Now getting & updating info.")
            self._get_and_update_info()
        except Exception as e:
            log.critical(
                "Something went wrong preparing the data for writing. "
                "However, no data has been written out, so your "
                "database is save!"
            )
            raise e
        else:
            log.debug("Successfully prepared data for writing.")

        if prepared == {}:
            log.warning(
                "Nothing seems to have been changed. Will not do anything!"
            )
            return None

        backup_path = ankipandas.paths.backup_db(
            self.path, backup_folder=backup_folder
        )
        log.info("Backup created at %s", backup_path.resolve())
        log.warning(
            "Currently AnkiPandas might not be able to tell Anki to"
            " sync its database. "
            "You might have to manually tell Anki to sync everything "
            "to AnkiDroid.\n"
            "Furthermore, if you run into issues with tag searches not working"
            "anymore, please first do Notes > Clear unused notes and then "
            "Tools > Check Database (from the main menu). This should get them"
            " to work (sorry about this issue)."
        )

        # Actually setting values here, after all conversion tasks have been
        # carried out. That way if any of them fails, we don't have a
        # partially written collection.
        log.debug("Now actually writing to database.")
        try:
            for table, values in prepared.items():
                log.debug("Now setting table %s.", table)
                with closing(self.db) as db:
                    raw.set_table(
                        db, values["raw"], table=table, mode=values["mode"]
                    )
                    log.debug("Setting table %s successful.", table)

                    if table == "cards":
                        raw.update_card_indices(db)

                    elif table == "notes":
                        raw.update_note_indices(db)

            # log.debug("Now setting info")
            # raw.set_info(self.db, info)
            # log.debug("Setting info successful.")
        except Exception as e:
            log.critical(
                "Error while writing data to database at %s. "
                "This means that your database might have become corrupted. "
                "It's STRONGLY advised that you manually restore the database "
                "by replacing it with the backup from %s and restart"
                " from scratch. "
                "Please also open a bug report at "
                "https://github.com/klieret/AnkiPandas/issues/, as errors "
                "during the actual writing process should never occur!",
                self.path.resolve(),
                backup_path.resolve(),
            )
            raise e
        # This is important, because we have written to the database but still
        # have it opened, which can cause DatabaseErrors.
        log.debug("I will now drop all copies of the tables")
        for key in self.__items:
            self.__items[key] = None
        for key in self.__original_items:
            self.__original_items[key] = None
        log.debug("I will now reload the connection.")
        self._db = raw.load_db(self.path)
        log.info(
            "In case you're running this from a Jupyter notebook, make "
            "sure to shutdown the kernel or delete all ankipandas objects"
            " before you open anki to take a look at the result (only one "
            "application can use the database at a time)."
        )
