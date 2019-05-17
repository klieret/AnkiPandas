#!/usr/bin/env python3

# std
import sqlite3
import time

# 3rd
import numpy as np
import pandas as pd
import pathlib
from typing import Union, List

# ours
import ankipandas.paths
import ankipandas.raw as raw
import ankipandas.util.dataframe
from ankipandas.util.dataframe import replace_df_inplace
import ankipandas._columns as _columns
from ankipandas.util.misc import invert_dict
from ankipandas.util.log import log
from ankipandas.util.checksum import field_checksum
from ankipandas.util.guid import guid


class AnkiDataFrame(pd.DataFrame):
    #: Additional attributes of a :class:`AnkiDataFrame` that a normal
    #: :class:`pandas.DataFrame` does not posess. These will be copied in the
    #: constructor.
    _attributes = ("db", "db_path", "_anki_table", "fields_as_columns_prefix",
                   "_fields_format", "_df_format")

    def __init__(self, *args, **kwargs):
        """ Initializes a blank :class:`AnkiDataFrame`.

        .. warning::

            It is recommended to directly initialize this class with the notes,
            cards or revs table, using one of the methods
            :meth:`.notes`, :meth:`.cards` or :meth:`.revs` instead!

        Args:
            *args: Internal use only. See arguments of
                :class:`pandas.DataFrame`.
            **kwargs: Internal use only. See arguments of
                :class:`pandas.DataFrame`.
        """
        super().__init__(*args, **kwargs)

        # IMPORTANT: Make sure to add all attributes to the class variable
        # :attr:`._attributes`. Also all of them have to be initialized as None!
        # (see the code where we copy attributes).

        #: Opened Anki database (:class:`sqlite3.Connection`)
        self.db = None  # type: sqlite3.Connection

        #: Path to Anki database that is opened as :attr:`.db`
        #:   (:class:`pathlib.Path`)
        self.db_path = None  # type: pathlib.Path

        #: Type of anki table: 'notes', 'cards' or 'revlog'. This corresponds to
        #: the meaning of the ID row.
        self._anki_table = None  # type: str

        #: Prefix for fields as columns. Default is ``nfld_``.
        self.fields_as_columns_prefix = "nfld_"

        #: Fields format: ``none``, ``list`` or ``columns`` or ``in_progress``,
        #:   or ``anki`` (default)
        self._fields_format = "anki"

        #: Overal structure of the dataframe ``anki``, ``ours``, ``in_progress``
        self._df_format = None  # type: str

        # todo: is this serving any purpose? Coverage shows it never runs.
        if len(args) == 1 and isinstance(args[0], AnkiDataFrame):
            self._copy_attrs_from(args[0])

    @property
    def _constructor(self):
        """ This needs to be overriden so that any DataFrame operations do not
        return a :class:`pandas.DataFrame` but a :class:`AnkiDataFrame`."""
        def __constructor(*args, **kw):
            df = self.__class__(*args, **kw)
            self._copy_attrs_to(df)
            return df
        return __constructor

    def _copy_attrs_to(self, df):
        """ Copy all additional attributes of this class to another instance.
        Also see :attr:`self._attributes`.
        """
        for attr in self._attributes:
            df.__dict__[attr] = getattr(self, attr, None)

    def _copy_attrs_from(self, df):
        """ Copy all additional attributes of this class from another instance.
        Also see :attr:`self._attributes`.
        """
        for attr in self._attributes:
            self.__dict__[attr] = getattr(df, attr, None)

    # Constructors
    # ==========================================================================

    def _load_db(self, path):
        self.db = raw.load_db(path)
        self.db_path = path

    def _get_table(self, path, user, table, empty):
        self._anki_table = table
        self._df_format = "anki"

        if not path:
            path = self.db_path
        self._load_db(ankipandas.paths.db_path_input(path, user=user))

        if empty:
            df = raw.get_empty_table(table)
        else:
            df = raw.get_table(self.db, table)

        replace_df_inplace(self, df)
        self.normalize(inplace=True)

    @classmethod
    def _table_constructor(cls, path, user, table, empty=False):
        new = AnkiDataFrame()
        new._get_table(path, user, table, empty=empty)
        return new

    @classmethod
    def notes(cls, path=None, user=None, empty=False):
        """ Initialize :class:`AnkiDataFrame` with notes table loaded from Anki
        database.

        Args:
            path: (Search) path to database see
                :py:func:`~ankipandas.paths.db_path_input` for more
                information.
            user: Anki user name. See
                :py:func:`~ankipandas.paths.db_path_input` for more
                information.
            empty: Return empty table.

        Example:

        .. code-block:: python

            import ankipandas
            notes = ankipandas.AnkiDataFrame.notes()

        """
        return cls._table_constructor(path, user, "notes", empty=empty)

    @classmethod
    def cards(cls, path=None, user=None, empty=False):
        """ Initialize :class:`AnkiDataFrame` with cards table loaded from Anki
        database.

        Args:
            path: (Search) path to database see
                :func:`~ankipandas.paths.db_path_input` for more
                information.
            user: Anki user name. See
                :func:`~ankipandas.paths.db_path_input` for more
                information.
            empty: Return empty table.

        Example:

        .. code-block:: python

            import ankipandas
            cards = ankipandas.AnkiDataFrame.cards()

        """
        if empty and (path is not None or user is not None):
            log.warning(
                "When initialized with empty==True, no database is "
                "initialized, so the path and user argument are ignored."
            )
        return cls._table_constructor(path, user, "cards", empty=empty)

    @classmethod
    def revs(cls, path=None, user=None, empty=False):
        """ Initialize :class:`AnkiDataFrame` with review table loaded from Anki
        database.

        Args:
            path: (Search) path to database see
                :func:`~ankipandas.paths.db_path_input` for more
                information.
            user: Anki user name. See
                :func:`~ankipandas.paths.db_path_input` for more
                information.
            empty: Return empty table.

        Example:

        .. code-block:: python

            import ankipandas
            revs = ankipandas.AnkiDataFrame.revs()

        """
        if empty and (path is not None or user is not None):
            log.warning(
                "When initialized with empty==True, no database is "
                "initialized, so the path and user argument are ignored."
            )
        return cls._table_constructor(path, user, "revs", empty=empty)

    # Fixes
    # ==========================================================================

    def equals(self, other):
        return pd.DataFrame(self).equals(other)

    def append(self, *args, **kwargs):
        ret = super(AnkiDataFrame, self).append(*args, **kwargs)
        self._copy_attrs_to(ret)
        ret.astype(_columns.dtype_casts2[self._anki_table])
        return ret

    def update(self, *args, **kwargs):
        super(AnkiDataFrame, self).update(*args, **kwargs)
        # Fix https://github.com/pandas-dev/pandas/issues/4094
        for col, typ in _columns.dtype_casts2[self._anki_table].items():
            self[col] = self[col].astype(typ)

    # ==========================================================================

    def _invalid_table(self):
        raise ValueError("Invalid table: {}.".format(self._anki_table))

    def _check_df_format(self):
        if self._df_format == "in_progress":
            raise ValueError(
                "Previous call to normalize() or raw() did not terminate "
                "succesfully. This is usually a very bad sign, but you can "
                "try calling them again with the force option: raw(force=True) "
                "or raw(force=True) and see if that works."
            )
        elif self._df_format == "anki":
            pass
        elif self._df_format == "ours":
            pass
        else:
            raise ValueError(
                "Unknown value of _df_format: {}".format(self._df_format)
            )

    def _check_our_format(self):
        self._check_df_format()
        if not self._df_format == "ours":
            raise ValueError(
                "This operation is not supported for AnkiDataFrames in the "
                "'raw' format. Perhaps you called raw() before or used the "
                "raw=True option when loading? You can try switching to the "
                "required format using the normalize() method."
            )

    # IDs
    # ==========================================================================

    @property
    def nid(self):
        """ Note ID as :class:`pandas.Series` of integers. """
        self._check_our_format()
        if self._anki_table == "notes":
            return self.index
        elif self._anki_table == "cards":
            if "nid" not in self.columns:
                raise ValueError(
                    "You seem to have removed the 'nid' column. That was not "
                    "a good idea. Cannot get note ID anymore."
                )
            else:
                return self["nid"]
        elif self._anki_table == "revs":
            if "nid" in self.columns:
                return self["nid"]
            else:
                return self.cid.map(raw.get_cid2nid(self.db))
        else:
            self._invalid_table()

    @nid.setter
    def nid(self, value):
        if self._anki_table == "notes":
            raise ValueError(
                "Note ID column should already be index and notes.nid() will "
                "always return this index. Therefore you should not set nid "
                "to a column."
            )
        else:
            self["nid"] = value

    @property
    def cid(self):
        """ Card ID as :class:`pandas.Series` of integers. """
        self._check_our_format()
        if self._anki_table == "cards":
            return self.index
        if self._anki_table == "revs":
            if "cid" not in self.columns:
                raise ValueError(
                    "You seem to have removed the 'cid' column. That was not "
                    "a good idea. Cannot get card ID anymore."
                )
            else:
                return self["cid"]
        elif self._anki_table == "notes":
            raise ValueError(
                "Notes can belong to multiple cards. Therefore it is impossible"
                " to associate a card ID with them."
            )
        else:
            self._invalid_table()

    @cid.setter
    def cid(self, value):
        if self._anki_table == "cards":
            raise ValueError(
                "Card ID column should already be index and notes.cid() will "
                "always return this index. Therefore you should not set cid "
                "to a column."
            )
        elif self._anki_table == "revs":
            self["cid"] = value
        else:
            raise ValueError(
                "Notes can belong to multiple cards. Therefore please "
                " do not associate a card ID with them."
            )

    @property
    def rid(self):
        """ Review ID as :class:`pandas.Series` of integers. """
        if self._anki_table == "revs":
            return self.index
        else:
            if "rid" in self.columns:
                return self["rid"]
            else:
                raise ValueError(
                    "Review index is only available for the 'revs' table by"
                    " default."
                )

    # noinspection PyUnusedLocal
    @rid.setter
    def rid(self, value):
        print("arg")
        if self._anki_table == "revs":
            raise ValueError(
                "Review ID column should already be index and notes.rid() will "
                "always return this index. Therefore you should not set rid "
                "to a column."
            )
        else:
            raise ValueError(
                "Setting a review index 'rid' makes no sense in "
                "tables other than 'rev'.")

    @property
    def mid(self):
        """ Model ID as :class:`pandas.Series` of integers. """
        self._check_our_format()
        if self._anki_table in ["notes"]:
            if "nmodel" not in self.columns:
                raise ValueError(
                    "You seem to have removed the 'nmodel' column. That was not"
                    " a good idea. Cannot get model ID anymore."
                )
            else:
                return self["nmodel"].map(raw.get_model2mid(self.db))
        if self._anki_table in ["revs", "cards"]:
            if "nmodel" in self.columns:
                return self["nmodel"].map(raw.get_model2mid(self.db))
            else:
                return self.nid.map(raw.get_nid2mid(self.db))
        else:
            self._invalid_table()

    @mid.setter
    def mid(self, value):
        if self._anki_table == "notes":
            log.warning(
                "You can set an additional 'mid' column, but this will always"
                " be overwritten with the information from the 'nmodel' "
                "column.")
        self["mid"] = value

    @property
    def did(self):
        """ Deck ID as :class:`pandas.Series` of integers. """
        self._check_our_format()
        if self._anki_table == "cards":
            if "cdeck" not in self.columns:
                raise ValueError(
                    "You seem to have removed the 'cdeck' column. That was not "
                    "a good idea. Cannot get deck ID anymore."
                )
            return self["cdeck"].map(raw.get_deck2did(self.db))
        elif self._anki_table == "notes":
            raise ValueError(
                "Notes can belong to multiple decks. Therefore it is impossible"
                " to associate a deck ID with them."
            )
        elif self._anki_table == "revs":
            return self.cid.map(raw.get_cid2did(self.db))
        else:
            self._invalid_table()

    @did.setter
    def did(self, value):
        if self._anki_table == "cards":
            log.warning(
                "You can set an additional deck ID 'did' column, but this "
                "will always be overwritten with the information from the "
                "'cdeck' column.")
        self["did"] = value

    @property
    def odid(self):
        """ Original deck ID for cards in filtered deck as
        :class:`pandas.Series` of integers.
        """
        self._check_our_format()
        if self._anki_table == "cards":
            if "odeck" not in self.columns:
                raise ValueError(
                    "You seem to have removed the 'odeck' column. That was not "
                    "a good idea. Cannot get original deck ID anymore."
                )
            return self["odeck"].map(raw.get_deck2did(self.db))
        elif self._anki_table == "revs":
            if "odeck" in self.columns:
                return self["odeck"].map(raw.get_deck2did(self.db))
        elif self._anki_table == "notes":
            raise ValueError(
                "The original deck ID (odid) is not availabale for the notes "
                "table."
            )
        else:
            self._invalid_table()

    @odid.setter
    def odid(self, value):
        if self._anki_table == "cards":
            log.warning(
                "You can set an additional 'odid' column, but this will always"
                " be overwritten with the information from the 'odeck' "
                "column."
            )
        self["odid"] = value

    # Merge tables
    # ==========================================================================

    def merge_notes(self, inplace=False, columns=None,
                    drop_columns=None, prepend="n",
                    prepend_clash_only=True):
        """ Merge note table into existing dataframe.

        Args:
            inplace: If False, return new dataframe, else update old one
            columns: Columns to merge
            drop_columns: Columns to ignore when merging
            prepend: Prepend this string to fields from note table
            prepend_clash_only: Only prepend the ``prepend`` string when column
                names would otherwise clash.

        Returns:
            New :class:`AnkiDataFrame` if inplace==True, else None
        """
        self._check_our_format()
        if self._anki_table == "notes":
            raise ValueError(
                "AnkiDataFrame was already initialized as a table of type"
                " notes, therefore merge_notes() doesn't make any sense."
            )
        elif self._anki_table == "revs":
            self["nid"] = self.nid
        return ankipandas.util.dataframe.merge_dfs(
            df=self,
            df_add=AnkiDataFrame.notes(self.db_path),
            id_df="nid",
            id_add="nid",
            inplace=inplace,
            prepend=prepend,
            prepend_clash_only=prepend_clash_only,
            columns=columns,
            drop_columns=drop_columns
        )

    def merge_cards(self, inplace=False, columns=None, drop_columns=None,
                    prepend="c", prepend_clash_only=True):
        """
        Merges information from the card table into the current dataframe.

        Args:
            inplace: If False, return new dataframe, else update old one
            columns:  Columns to merge
            drop_columns:  Columns to ignore when merging
            prepend: Prepend this string to fields from card table
            prepend_clash_only: Only prepend the ``prepend`` string when column
                names would otherwise clash.

        Returns:
            New :class:`AnkiDataFrame` if inplace==True, else None
        """
        if self._anki_table == "cards":
            raise ValueError(
                "AnkiDataFrame was already initialized as a table of type"
                " cards, therefore merge_cards() doesn't make any sense."
            )
        elif self._anki_table == "notes":
            raise ValueError(
                "One note can correspond to more than one card, therefore it "
                "it is not supported to merge the cards table into the "
                "notes table."
            )
        self._check_our_format()
        return ankipandas.util.dataframe.merge_dfs(
            df=self,
            df_add=AnkiDataFrame.cards(self.db_path),
            id_df="cid",
            inplace=inplace,
            columns=columns,
            drop_columns=drop_columns,
            id_add="cid",
            prepend=prepend,
            prepend_clash_only=prepend_clash_only
        )

    # Toggle format
    # ==========================================================================

    def fields_as_columns(self, inplace=False):
        """
        In the 'notes' table, the field contents of the notes is contained in
        one column ('flds') by default. With this method, this column can be
        split up into a new column for every field.

        Args:
            inplace: If False, return new dataframe, else update old one

        Returns:
            New :class:`pandas.DataFrame` if inplace==True, else None
        """
        self._check_our_format()
        if not inplace:
            df = self.copy(True)
            df.fields_as_columns(inplace=True)
            return df

        if "nflds" not in self.columns:
            raise ValueError(
                "Could not find fields column 'nflds'."
            )

        if self._fields_format == "columns":
            log.warning(
                "Fields are already as columns."
                " Returning without doing anything."
            )
            return
        elif self._fields_format == "in_progress":
            raise ValueError(
                "It looks like the last call to fields_as_list or"
                "fields_as_columns was not successful, so you better start "
                "over."
            )
        elif self._fields_format == "list":
            pass
        else:
            raise ValueError(
                "Unknown _fields_format: {}".format(self._fields_format)
            )

        self._fields_format = "in_progress"
        # fixme: What if one field column is one that is already in use?
        prefix = self.fields_as_columns_prefix
        mids = self.mid.unique()
        for mid in mids:
            if mid == 0:
                continue
            df_model = self[self.mid == mid]
            fields = pd.DataFrame(df_model["nflds"].tolist())
            field_names = raw.get_mid2fields(self.db)[mid]
            for field in field_names:
                if prefix + field not in self.columns:
                    self[prefix + field] = ""
            for ifield, field in enumerate(field_names):
                self.loc[self.mid == mid, [prefix + field]] = \
                    fields[ifield].tolist()
        self.drop("nflds", axis=1, inplace=True)
        self._fields_format = "columns"

    def fields_as_list(self, inplace=False):
        """
        This reverts :meth:`.fields_as_columns`, all columns that represented
        field contents are now merged into one column 'nflds'.

        Args:
            inplace: If False, return new dataframe, else update old one

        Returns:
            New :class:`AnkiDataFrame` if inplace==True, else None
        """
        self._check_our_format()
        if not inplace:
            df = self.copy()  # deep?
            df.fields_as_list(
                inplace=True,
            )
            return df

        if self._fields_format == "list":
            log.warning(
                "Fields are already as list. Returning without doing anything."
            )
            return
        elif self._fields_format == "in_progress":
            raise ValueError(
                "It looks like the last call to fields_as_list or"
                "fields_as_columns was not successful, so you better start "
                "over."
            )
        elif self._fields_format == "columns":
            pass
        else:
            raise ValueError(
                "Unknown _fields_format: {}".format(self._fields_format)
            )

        self._fields_format = "in_progress"
        mids = self.mid.unique()
        to_drop = []
        for mid in mids:
            fields = raw.get_mid2fields(self.db)[mid]
            fields = [
                self.fields_as_columns_prefix + field for field in fields
            ]
            self.loc[self.mid == mid, "nflds"] = \
                pd.Series(
                    self.loc[self.mid == mid, fields].values.tolist(),
                    index=self.loc[self.mid == mid].index
                )
            # Careful: Do not delete the fields here yet, other models
            # might still use them
            to_drop.extend(fields)
        self.drop(to_drop, axis=1, inplace=True)
        self._fields_format = "fields"

    # Quick access
    # ==========================================================================

    def _check_tag_col(self):
        if "ntags" not in self.columns:
            raise ValueError(
                "Tag column 'ntags' doesn't exist. Perhaps you forgot to merge "
                "the notes into your table?"
            )

    def list_tags(self) -> List[str]:
        """ Return sorted list of all tags. """
        if "ntags" not in self.columns:
            raise ValueError(
                "Tags column 'ntags' not present. Either use the notes table"
                " or merge it into your table."
            )
        else:
            return sorted(list(set(
                [item for lst in self["ntags"].tolist() for item in lst]
            )))

    def list_decks(self):
        """ Return sorted list of deck names. """
        decks = sorted(list(raw.get_did2deck(self.db).values()))
        if "" in decks:
            decks.remove("")
        return decks

    def list_models(self):
        """ Return sorted list of model names. """
        return sorted(list(raw.get_mid2model(self.db).values()))

    def has_tag(self, tags=None):
        """ Checks whether row has a certain tag ('ntags' column).

        Args:
            tags: String or list thereof. In the latter case, True is returned
                if the row contains any of the specified tags.
                If None (default), True is returned if the row has any tag at
                all.

        Returns:
            Boolean :class:`pd.Series`

        Examples:

            .. code-block::

                # Get all tagged notes:
                notes[notes.has_tag()]
                # Get all untagged notes:
                notes[~notes.has_tag()]
                # Get all notes tagged Japanese:
                japanese_notes = notes[notes.has_tag("Japanese")]
                # Get all notes tagged either Japanese or Chinese:
                asian_notes = notes[notes.has_tag(["Japanese", "Chinese"])]
        """
        self._check_our_format()
        self._check_tag_col()

        if isinstance(tags, str):
            tags = [tags]

        if tags is not None:

            def _has_tag(other):
                return not set(tags).isdisjoint(other)

            return self["ntags"].apply(_has_tag)

        else:
            return self["ntags"].apply(bool)

    def has_tags(self, tags=None):
        """ Checks whether row contains at least the supplied tags.

        Args:
            tags: String or list thereof.
                If None (default), True is returned if the row has any tag at
                all.

        Returns:
            Boolean :class:`pd.Series`

        Examples:

            .. code-block::

                # Get all notes tagged BOTH Japanese or Chinese
                bilingual_notes = notes[notes.has_tags(["Japanese", "Chinese"])]
                # Note the difference to
                asian_notes = notes[notes.has_tag(["Japanese", "Chinese"])]
        """
        self._check_our_format()
        if tags is None:
            return self.has_tag(None)
        self._check_tag_col()
        if isinstance(tags, str):
            tags = [tags]
        _has_tags = set(tags).issubset
        return self["ntags"].apply(_has_tags)

    def add_tag(self, tags, inplace=False):
        """ Adds tag ('ntags' column).

        Args:
            tags: String or list thereof.
            inplace: If False, return new dataframe, else update old one

        Returns:
            New :class:`AnkiDataFrame` if inplace==True, else None
        """
        self._check_our_format()
        if not inplace:
            df = self.copy()  # deep?
            df.add_tag(tags, inplace=True)
            return df

        self._check_tag_col()
        if isinstance(tags, str):
            tags = [tags]

        if len(tags) == 0:
            return

        def _add_tags(other):
            return other + sorted(list(set(tags) - set(other)))

        self["ntags"] = self["ntags"].apply(_add_tags)

    def remove_tag(self, tags, inplace=False):
        """ Removes tag ('ntags' column).

        Args:
            tags: String or list thereof. If None, all tags are removed.
            inplace: If False, return new dataframe, else update old one

        Returns:
            New :class:`AnkiDataFrame` if inplace==True, else None
        """
        self._check_our_format()
        if not inplace:
            df = self.copy()  # deep?
            df.remove_tag(tags, inplace=True)
            return df

        self._check_tag_col()
        if isinstance(tags, str):
            tags = [tags]

        if tags is not None:

            def _remove_tags(other):
                return [tag for tag in other if tag not in tags]

            self["ntags"] = self["ntags"].apply(_remove_tags)

        else:
            self["ntags"] = self["ntags"].apply(lambda _: [])

    # Compare
    # ==========================================================================

    # todo: other comparison source
    def was_modified(self, other: pd.DataFrame = None, na=True,
                     _force=False):
        """ Compare with original table, show which rows have changed.

        Args:
            other: Compare with this :class:`pandas.DataFrame`.
                If None (default), use original unmodified dataframe as reloaded
                from the database.
            na: Value for new or deleted columns
            _force: internal use

        Returns:
            Boolean value for each row, showing if it was modified.
        """
        if not _force:
            self._check_our_format()

        if other is None:
            other = self._table_constructor(
                self.db_path, None, self._anki_table
            )

        other_nids = set(other.index)
        inters = set(self.index).intersection(other_nids)
        result = pd.Series(na, index=self.index)
        new_bools = np.any(
            other[other.index.isin(inters)].values !=
            self[self.index.isin(inters)].values,
            axis=1
        )
        result.loc[self.index.isin(inters)] = pd.Series(
            new_bools,
            index=result[self.index.isin(inters)].index
        )
        return result

    def modified_columns(self, other: pd.DataFrame = None, _force=False,
                         only=True):
        """ Compare with original table, show which rows were added.

        Args:
            other: Compare with this :class:`pandas.DataFrame`.
                If None (default), use original unmodified dataframe as reloaded
                from the database.
            only: Only show rows where at least one column is changed.
            _force: internal use

        Returns:
            Boolean value for each row, showing if it was modified. New rows
            are considered to be modified as well.
        """
        if other is None:
            other = self._table_constructor(
                self.db_path, None, self._anki_table
            )
        cols = [c for c in self.columns if c in other.columns]
        other_nids = set(other.index)
        inters = set(self.index).intersection(other_nids)
        if only:
            inters = inters.intersection(
                self[self.was_modified(other=other, _force=_force)].index
            )
        inters = sorted(list(inters))
        return pd.DataFrame(
            self.loc[inters, cols].values != other.loc[inters, cols].values,
            index=self.loc[inters].index,
            columns=cols
        )

    def was_added(self, other: pd.DataFrame = None, _force=False):
        """ Compare with original table, show which rows were added.

        Args:
            other: Compare with this :class:`pandas.DataFrame`.
                If None (default), use original unmodified dataframe as reloaded
                from the database.
            _force: internal use

        Returns:
            Boolean value for each row, showing if it was modified. New rows
            are considered to be modified as well.
        """
        if not _force:
            self._check_our_format()

        if other is not None:
            other_nids = set(other.index)
        else:
            other_nids = set(raw.get_ids(self.db, self._anki_table))

        new_indices = set(self.index) - other_nids
        return self.index.isin(new_indices)

    def was_deleted(self, other: pd.DataFrame = None, _force=False):
        """ Compare with original table, return deleted indizes.

        Args:
            other: Compare with this :class:`pandas.DataFrame`.
                If None (default), use original unmodified dataframe as reloaded
                from the database.
            _force: internal use

        Returns:
            Sorted list of indizes.
        """
        if not _force:
            self._check_our_format()

        if other is not None:
            other_nids = set(other.index)
        else:
            other_nids = set(raw.get_ids(self.db, self._anki_table))

        deleted_indices = other_nids - set(self.index)
        return sorted(list(deleted_indices))

    # Update modification stamps and similar
    # ==========================================================================

    def _set_usn(self):
        """ Update usn (update sequence number) for all changed rows. """
        self.loc[
            self.was_modified(na=True, _force=True),
            _columns.columns_anki2ours[self._anki_table]["usn"]
        ] = -1

    def _set_mod(self):
        """ Update modification timestamps for all changed rows. """
        if self._anki_table in ["cards", "notes"]:
            self.loc[
                self.was_modified(na=True, _force=True),
                _columns.columns_anki2ours[self._anki_table]["mod"]
            ] = int(time.time())

    # todo: test
    def _set_guid(self):
        """ Update globally unique id """
        if self._anki_table == "notes":
            self.loc[~self["nguid"].apply(bool)].apply(guid)

    # Raw and normalized
    # ==========================================================================

    def normalize(self, inplace=False, force=False):
        """ Bring a :class:`AnkiDataFrame` from the ``raw`` format (i.e. the
        exact format that Anki uses in its internal representation) to our
        convenient format.

        Args:
            inplace: If False, return new dataframe, else update old one
            force: If a previous conversion fails, :meth:`normalize` will
                refuse to attempt another one by default. Use this option
                to force it to attempt in anyway.

        Returns:
            New :class:`AnkiDataFrame` if inplace==True, else None
        """
        if not inplace:
            df = self.copy()
            df.normalize(inplace=True, force=force)
            return df

        if not force:
            self._check_df_format()
            if self._df_format == "ours":
                log.warning(
                    "Dataframe already is in our format. "
                    "Returning without doing anything."
                )
                return

        table = self._anki_table
        if table not in ["cards", "revs", "notes"]:
            self._invalid_table()

        self._df_format = "in_progress"

        # Dtypes
        # ------

        for column, typ in _columns.dtype_casts[table].items():
            self[column] = self[column].astype(typ)

        # Renames
        # -------

        self.rename(
            columns=_columns.columns_anki2ours[table],
            inplace=True
        )

        # Value maps
        # ----------
        # We sometimes interpret cryptic numeric values

        if table in _columns.value_maps:
            for column in _columns.value_maps[table]:
                self[column] = self[column].map(
                    _columns.value_maps[table][column]
                )

        # IDs
        # ---

        self.set_index(_columns.table2index[table], inplace=True)

        if table == "cards":
            self["cdeck"] = self["did"].map(raw.get_did2deck(self.db))
            self["codeck"] = self["codid"].map(raw.get_did2deck(self.db))
        elif table == "notes":
            self["nmodel"] = self["mid"].map(raw.get_mid2model(self.db))

        # Tags
        # ----

        if table == "notes":
            # Tags as list, rather than string joined by space
            self["ntags"] = \
                self["ntags"].apply(
                    lambda joined: [item for item in joined.split(" ") if item]
                )

        # Fields
        # ------

        if table == "notes":
            # Fields as list, rather than as string joined by \x1f
            self["nflds"] = self["nflds"].str.split("\x1f")
            self._fields_format = "list"

        # Drop columns
        # ------------

        drop_columns = \
            set(self.columns) - set(_columns.our_columns[table])
        self.drop(drop_columns, axis=1, inplace=True)

        self._df_format = "ours"

    def raw(self, inplace=False, force=False):
        """ Bring a :class:`AnkiDataFrame` into the ``raw`` format (i.e. the
        exact format that Anki uses in its internal representation) .

        Args:
            inplace: If False, return new dataframe, else update old one
            force: If a previous conversion fails, :meth:`raw` will
                refuse to attempt another one by default. Use this option
                to force it to attempt in anyway.

        Returns:
            New :class:`AnkiDataFrame` if inplace==True, else None
        """
        if not inplace:
            df = self.copy()  # deep?
            df.raw(inplace=True, force=force)
            return df

        if not force:
            self._check_df_format()
            if self._df_format == "anki":
                log.warning(
                    "Dataframe already is in Anki format. "
                    "Returning without doing anything."
                )
                return

        table = self._anki_table
        if table not in ["revs", "cards", "notes"]:
            self._invalid_table()

        self._df_format = "in_progress"

        # Note: Here we pretty much go through self.normalize() and revert
        # every single step.

        # Update automatic fields
        # -----------------------

        self._set_mod()
        self._set_usn()
        self._set_guid()

        # IDs
        # ---

        # Index as column:
        self.reset_index(inplace=True, drop=False)

        if table == "cards":
            self["did"] = self["cdeck"].map(
                raw.get_deck2did(self.db)
            )
            self["odid"] = self["codeck"].map(
                raw.get_deck2did(self.db)
            )
        if table == "notes":
            self["mid"] = self["nmodel"].map(
                raw.get_model2mid(self.db)
            )

        # Fields & Hashes
        # ---------------

        if table == "notes":
            if not self._fields_format == "list":
                self.fields_as_columns(inplace=True)
            # Check if success
            if not self._fields_format == "list":
                raise ValueError(
                    "It looks like the last call to fields_as_list or"
                    "fields_as_columns was not successful, so you better start "
                    "over."
                )

            # Restore the sort field.
            mids = list(self["mid"].unique())
            mid2sfld = raw.get_mid2sortfield(self.db)
            for mid in mids:
                sfield = mid2sfld[mid]
                df_model = self[self["mid"] == mid]
                fields = pd.DataFrame(df_model["nflds"].tolist())
                self.loc[self["mid"] == mid, "nsfld"] = fields[sfield].tolist()

            self["ncsum"] = self["nflds"].apply(
                lambda lst: field_checksum(lst[0])
            )

            self["nflds"] = self["nflds"].str.join("\x1f")

        # Tags
        # ----

        if table == "notes" and "nflds" in self.columns:
            self["ntags"] = self["ntags"].str.join(" ")

        # Value Maps
        # ----------

        if table in _columns.value_maps:
            for column in _columns.value_maps[table]:
                if column not in self.columns:
                    continue
                self[column] = self[column].map(
                    invert_dict(_columns.value_maps[table][column])
                )

        # Renames
        # -------

        self.rename(
            columns=invert_dict(_columns.columns_anki2ours[table]),
            inplace=True
        )

        # Dtypes
        # ------

        for column, typ in _columns.dtype_casts_back[table].items():
            self[column] = self[column].astype(typ)

        # Unused columns
        # --------------

        if table in ["cards", "notes"]:
            self["data"] = ""
            self["flags"] = 0

        # Drop and Rearrange
        # ------------------

        if len(self) == 0:
            new = pd.DataFrame(columns=_columns.anki_columns[table])
        else:
            new = pd.DataFrame(
                self[_columns.anki_columns[table]]
            )
        self.drop(self.columns, axis=1, inplace=True)
        for col in new.columns:
            self[col] = new[col]

        self._df_format = "anki"

    # Write
    # ==========================================================================

    def write(self, mode, backup_folder: Union[pathlib.PurePath, str] = None):
        """ Creates a backup of the database and then writes back the new
        data.

        Args:
            mode: ``update``: Update only existing entries, ``append``: Only
                append new entries, but do not modify,
                ``replace``: Append, modify and delete
            backup_folder: Path to backup folder. If None is given, the backup
                is created in the Anki backup directory (if found).

        Returns:
            None
        """
        backup_path = ankipandas.paths.backup_db(
            self.db_path, backup_folder=backup_folder
        )
        log.info("Backup created at {}.".format(backup_path.resolve()))
        raw.set_table(self.db, self.raw(), table=self._anki_table, mode=mode)

    # Help
    # ==========================================================================

    def help_col(self, column, ret=False) -> Union[str, None]:
        """
        Show description/help about a column. To get information about all
        columns, use the :meth:`.help_cols` method instead.

        Args:
              column: Name of the column
              ret: If True, return as string, rather than printing
        """
        df = self.help_cols(column)
        if len(df) == 0:
            raise ValueError(
                "Could not find help for your search request.".format(column)
            )
        if len(df) == 2:
            # fix for nid and cid column:
            df = self.help_cols(column, table=self._anki_table)
        if len(df) != 1:
            raise ValueError("Could not find help due to bug.")
        data = df.loc[column].to_dict()
        h = "Help for column '{}'\n".format(column)
        h += "-" * (len(h) - 1) + "\n"
        if data["Native"]:
            h += "Name in raw Anki database: " + data["AnkiColumn"] + "\n"
        h += "Information from table: " + data["Table"] + "\n"
        h += "Present by default: " + str(data["Default"]) + "\n\n"
        h += "Description: " + data["Description"]
        if ret:
            return h
        else:
            print(h)

    def help_cols(self, column='auto', table='all', ankicolumn='all') \
            -> pd.DataFrame:
        """
        Show information about the columns and their interpretations. To
        get information about a single column, please use :meth:`.help_col`.

        Args:
            column: Name of a field or column (as used by us) or list thereof.
                If 'auto' (default), all columns from the current dataframe will
                be shown.
                If 'all' no filtering based on the table will be performed
            table: Possible values: 'notes', 'cards', 'revlog' or list thereof.
                If 'all' no filtering based on the table will be performed
            ankicolumn: Name of a field or column (as used by Anki) or list
                thereof.
                If 'all' no filtering based on the table will be performed

        Returns:
            Pandas DataFrame with all matches.

        .. warning::

            As there are problems with text wrapping in pandas DataFrame, this
            method might change or disappear in the future.
        """
        help_path = pathlib.Path(__file__).parent / "data" / "anki_fields.csv"
        df = pd.read_csv(help_path)
        if column == 'auto':
            column = list(self.columns)
        if table is not 'all':
            if isinstance(table, str):
                table = [table]
            df = df[df["Table"].isin(table)]
        if column is not 'all':
            if isinstance(column, str):
                column = [column]
            df = df[df["Column"].isin(column)]
        if ankicolumn is not 'all':
            if isinstance(ankicolumn, str):
                ankicolumn = [ankicolumn]
            df = df[df["AnkiColumn"].isin(ankicolumn)]
        df.set_index("Column", inplace=True)
        return df

    @staticmethod
    def help(ret=False) -> Union[str, None]:
        """ Display short help text.

        Args:
            ret: Return as string instead of printing it.

        Returns:
            string if ret==True, else None
        """
        h = "This is the help for the class AnkiDataFrame, a subclass of " \
            "pandas.DataFrame. \n" \
            "The full documentation of all class methods " \
            "unique to AnkiDataFrame can be found on " \
            "https://ankipandas.readthedocs.io. \n" \
            "The inherited methods from " \
            "pandas.DataFrame are documented at https://pandas.pydata.org/" \
            "pandas-docs/stable/reference/api/pandas.DataFrame.html.\n" \
            "To get information about the fields currently in this table, " \
            "please use the help_cols() method."
        if ret:
            return h
        else:
            print(h)
