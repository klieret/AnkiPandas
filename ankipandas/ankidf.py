#!/usr/bin/env python3

# std
import copy
import time

# 3rd
import numpy as np
import pandas as pd
import pathlib
from typing import Union, List, Dict, Optional, Iterable

# ours
import ankipandas.paths
import ankipandas.raw as raw
import ankipandas.util.dataframe
from ankipandas.util.dataframe import replace_df_inplace
import ankipandas._columns as _columns
from ankipandas.util.misc import invert_dict, flatten_list_list
from ankipandas.util.log import log
from ankipandas.util.checksum import field_checksum
from ankipandas.util.guid import guid as generate_guid
from ankipandas.util.types import (
    is_list_list_like,
    is_list_like,
    is_list_dict_like,
    is_dict_list_like,
)


class AnkiDataFrame(pd.DataFrame):
    #: Additional attributes of a :class:`AnkiDataFrame` that a normal
    #: :class:`pandas.DataFrame` does not possess. These will be copied in the
    #: constructor.
    #: See https://pandas.pydata.org/pandas-docs/stable/development/extending.html
    _metadata = [
        "col",
        "_anki_table",
        "fields_as_columns_prefix",
        "_fields_format",
        "_df_format",
    ]

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

        # todo: document
        self.col = None

        # noinspection PyTypeChecker
        # gets set by _get_table
        #: Type of anki table: 'notes', 'cards' or 'revlog'. This corresponds to
        #: the meaning of the ID row.
        self._anki_table = None  # type: str

        #: Prefix for fields as columns. Default is ``nfld_``.
        self.fields_as_columns_prefix = "nfld_"

        #: Fields format: ``none``, ``list`` or ``columns`` or ``in_progress``,
        #:   or ``anki`` (default)
        self._fields_format = "anki"

        # gets set by _get_table
        # noinspection PyTypeChecker
        #: Overal structure of the dataframe ``anki``, ``ours``, ``in_progress``
        self._df_format = None  # type: str

    @property
    def _constructor(self):
        """ This needs to be overriden so that any DataFrame operations do not
        return a :class:`pandas.DataFrame` but a :class:`AnkiDataFrame`."""

        return AnkiDataFrame

    # Constructors
    # ==========================================================================

    def _get_table(self, col, table, empty=False):
        self._anki_table = table
        self._df_format = "anki"
        self.col = col

        if empty:
            df = raw.get_empty_table(table)
        else:
            df = raw.get_table(col.db, table)

        replace_df_inplace(self, df)
        self.normalize(inplace=True)

    @classmethod
    def init_with_table(cls, col, table, empty=False):
        new = AnkiDataFrame()
        new._get_table(col, table, empty=empty)
        return new

    # Fixes
    # ==========================================================================

    def equals(self, other):
        return pd.DataFrame(self).equals(other)

    def append(self, *args, **kwargs):
        ret = pd.DataFrame.append(self, *args, **kwargs)
        ret.astype(_columns.dtype_casts2[self._anki_table])
        return ret

    def update(self, other, force=False, **kwargs):
        if not force and isinstance(other, AnkiDataFrame):
            if other._df_format != self._df_format:
                raise ValueError(
                    "You're trying to update an AnkiDataFrame in format {f1}"
                    " using another AnkiDataFrame in format {f2}. That doesn't "
                    "sound like a good idea. However you can still do this "
                    "using the force=True option.".format(
                        f1=self._df_format, f2=other._df_format
                    )
                )
            if other._anki_table != self._anki_table:
                raise ValueError(
                    "You're trying to update an AnkiDataFrame of table {f1} "
                    "with an AnkiDataFrame of table {f2}. That doesn't sound"
                    " like a good idea. However you can still do this using "
                    "the force=True option.".format(
                        f1=self._anki_table, f2=other._anki_table
                    )
                )
            if self._anki_table == "notes":
                if other._fields_format != self._fields_format:
                    raise ValueError(
                        "You are trying to update a notes AnkiDataFrame where "
                        "the fields are in format '{f1}' with a notes "
                        "AnkiDataFrame where the fields are in format '{f2}'. "
                        "That doesn't sound like a good idea. However you can "
                        "still do this using the force=True option. "
                        "Or you simply ensure that both have the same format"
                        " using the fields_as_columns() or fields_as_list() "
                        "method.".format(
                            f1=self._fields_format, f2=other._fields_format
                        )
                    )
        super(AnkiDataFrame, self).update(other, **kwargs)
        # Fix https://github.com/pandas-dev/pandas/issues/4094
        for col, typ in _columns.dtype_casts2[self._anki_table].items():
            self[col] = self[col].astype(typ)

    # Checks
    # ==========================================================================

    def check_table_integrity(self):
        duplicates = self.index[self.index.duplicated()].tolist()
        if duplicates:
            log.critical(
                "Duplicated indizes in table {} discovered, so something "
                "definitely went wrong. Please don't ignore this warning. "
                "These indizes appear more "
                "than once: {}".format(
                    self._anki_table, ", ".join(map(str, duplicates))
                )
            )

    def _invalid_table(self):
        raise ValueError("Invalid table: {}.".format(self._anki_table))

    def _check_df_format(self):
        if self._df_format == "in_progress":
            raise ValueError(
                "Previous call to normalize() or raw() did not terminate "
                "successfully. This is usually a very bad sign, but you can "
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

    # Properties
    # ==========================================================================

    @property
    def db(self):
        """Opened Anki database (:class:`sqlite3.Connection`)"""
        return self.col.db

    # IDs
    # ==========================================================================

    @property
    def id(self):
        """ Return note/card/review ID as :class:`pandas.Series` of integers.
        """
        if self._anki_table == "notes":
            return self.nid
        elif self._anki_table == "cards":
            return self.cid
        elif self._anki_table == "revs":
            return self.rid
        else:
            self._invalid_table()

    @property
    def nid(self):
        """ Note ID as :class:`pandas.Series` of integers. """
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
        if self._anki_table == "revs":
            raise ValueError(
                "Review ID column should already be index and notes.rid() will "
                "always return this index. Therefore you should not set rid "
                "to a column."
            )
        else:
            raise ValueError(
                "Setting a review index 'rid' makes no sense in "
                "tables other than 'rev'."
            )

    @property
    def mid(self):
        """ Model ID as :class:`pandas.Series` of integers. """
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
                "column."
            )
        self["mid"] = value

    @property
    def did(self):
        """ Deck ID as :class:`pandas.Series` of integers. """
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
                "'cdeck' column."
            )
        self["did"] = value

    @property
    def odid(self):
        """ Original deck ID for cards in filtered deck as
        :class:`pandas.Series` of integers.
        """
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
                "The original deck ID (odid) is not available for the notes "
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

    def merge_notes(
        self,
        inplace=False,
        columns=None,
        drop_columns=None,
        prepend="n",
        prepend_clash_only=True,
    ):
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
        ret = ankipandas.util.dataframe.merge_dfs(
            df=self,
            df_add=self.col.notes,
            id_df="nid",
            id_add="nid",
            inplace=inplace,
            prepend=prepend,
            prepend_clash_only=prepend_clash_only,
            columns=columns,
            drop_columns=drop_columns,
        )
        return ret

    def merge_cards(
        self,
        inplace=False,
        columns=None,
        drop_columns=None,
        prepend="c",
        prepend_clash_only=True,
    ):
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
        ret = ankipandas.util.dataframe.merge_dfs(
            df=self,
            df_add=self.col.cards,
            id_df="cid",
            inplace=inplace,
            columns=columns,
            drop_columns=drop_columns,
            id_add="cid",
            prepend=prepend,
            prepend_clash_only=prepend_clash_only,
        )
        return ret

    # Toggle format
    # ==========================================================================

    def fields_as_columns(self, inplace=False, force=False):
        """
        In the 'notes' table, the field contents of the notes is contained in
        one column ('flds') by default. With this method, this column can be
        split up into a new column for every field.

        Args:
            inplace: If False, return new dataframe, else update old one
            force: Internal use

        Returns:
            New :class:`pandas.DataFrame` if inplace==True, else None
        """
        if not force:
            self._check_our_format()
        if not inplace:
            df = self.copy(True)
            df.fields_as_columns(inplace=True)
            return df

        if self._fields_format == "columns":
            log.warning(
                "Fields are already as columns."
                " Returning without doing anything."
            )
            return
        elif self._fields_format == "in_progress" and not force:
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

        if "nflds" not in self.columns:
            raise ValueError("Could not find fields column 'nflds'.")

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
                # todo: can we speed this up?
                self.loc[self.mid == mid, [prefix + field]] = pd.Series(
                    fields[ifield].tolist(),
                    index=self.loc[self.mid == mid].index,
                )
        self.drop("nflds", axis=1, inplace=True)
        self._fields_format = "columns"

    def fields_as_list(self, inplace=False, force=False):
        """
        This reverts :meth:`.fields_as_columns`, all columns that represented
        field contents are now merged into one column 'nflds'.

        Args:
            inplace: If False, return new dataframe, else update old one
            force: Internal use

        Returns:
            New :class:`AnkiDataFrame` if inplace==True, else None
        """
        if not force:
            self._check_our_format()
        if not inplace:
            df = self.copy(True)
            df.fields_as_list(inplace=True, force=force)
            return df

        if self._fields_format == "list":
            log.warning(
                "Fields are already as list. Returning without doing anything."
            )
            return
        elif self._fields_format == "in_progress" and not force:
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
            fields = [self.fields_as_columns_prefix + field for field in fields]
            self.loc[self.mid == mid, "nflds"] = pd.Series(
                self.loc[self.mid == mid, fields].values.tolist(),
                index=self.loc[self.mid == mid].index,
            )
            # Careful: Do not delete the fields here yet, other models
            # might still use them
            to_drop.extend(fields)
        self.drop(to_drop, axis=1, inplace=True)
        self._fields_format = "list"

    # Quick access
    # ==========================================================================

    def _check_tag_col(self):
        if "ntags" not in self.columns:
            raise ValueError(
                "Tag column 'ntags' doesn't exist. Perhaps you forgot to merge "
                "the notes into your table?"
            )

    def list_tags(self) -> List[str]:
        """ Return sorted list of all tags in the current table. """
        if "ntags" not in self.columns:
            raise ValueError(
                "Tags column 'ntags' not present. Either use the notes table"
                " or merge it into your table."
            )
        else:
            return sorted(
                list(
                    set(
                        [item for lst in self["ntags"].tolist() for item in lst]
                    )
                )
            )

    def list_decks(self) -> List[str]:
        """ Return sorted list of deck names in the current table. """
        if "cdeck" not in self.columns:
            raise ValueError(
                "Deck column 'cdeck' not present. Either use the cards table "
                "or merge it into your table."
            )
        else:
            decks = sorted(list(self["cdeck"].unique()))
            if "" in decks:
                decks.remove("")
            return decks

    def list_models(self):
        """ Return sorted list of model names in the current table. """
        if "nmodel" not in self.columns:
            raise ValueError(
                "Model column 'nmodel' not present. Either use the notes table"
                " or merge it into your table."
            )
        return sorted(list(self["nmodel"].unique()))

    def has_tag(self, tags: Optional[Union[Iterable[str], str]] = None):
        """ Checks whether row has a certain tag ('ntags' column).

        Args:
            tags: String or list thereof. In the latter case, True is returned
                if the row contains any of the specified tags.
                If None (default), True is returned if the row has any tag at
                all.

        Returns:
            Boolean :class:`pd.Series`

        Examples:

            .. code-block:: python

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

    def has_tags(self, tags: Optional[Union[Iterable[str], str]] = None):
        """ Checks whether row contains at least the supplied tags.

        Args:
            tags: String or list thereof.
                If None (default), True is returned if the row has any tag at
                all.

        Returns:
            Boolean :class:`pd.Series`

        Examples:

            .. code-block:: python

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

    def add_tag(self, tags: Union[Iterable[str], str], inplace=False):
        """ Adds tag ('ntags' column).

        Args:
            tags: String or list thereof.
            inplace: If False, return new dataframe, else update old one

        Returns:
            New :class:`AnkiDataFrame` if inplace==True, else None
        """
        self._check_our_format()
        if not inplace:
            df = self.copy(True)
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

    def remove_tag(self, tags: Union[Iterable[str], str, None], inplace=False):
        """ Removes tag ('ntags' column).

        Args:
            tags: String or list thereof. If None, all tags are removed.
            inplace: If False, return new dataframe, else update old one

        Returns:
            New :class:`AnkiDataFrame` if inplace==True, else None
        """
        self._check_our_format()
        if not inplace:
            df = self.copy(True)
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

    def was_modified(
        self, other: Optional[pd.DataFrame] = None, na=True, _force=False
    ):
        """ Compare with original table, show which rows have changed.
        Will only compare columns existing in both dataframes.

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
            other = self.col._get_original_item(
                self._anki_table
            )  # type: AnkiDataFrame

        self_sf = self
        if self._fields_format == "columns":
            self_sf = self.fields_as_list(inplace=False, force=_force)

        cols = sorted(
            list(set(self_sf.columns).intersection(set(other.columns)))
        )

        other_nids = set(other.index)
        inters = set(self_sf.index).intersection(other_nids)
        result = pd.Series(na, index=self_sf.index)
        new_bools = np.any(
            other.loc[other.index.isin(inters), cols].values
            != self_sf.loc[self_sf.index.isin(inters), cols].values,
            axis=1,
        )
        result.loc[self_sf.index.isin(inters)] = pd.Series(
            new_bools, index=result[self_sf.index.isin(inters)].index
        )
        return result

    def modified_columns(
        self, other: Optional[pd.DataFrame] = None, _force=False, only=True
    ):
        """ Compare with original table, show which columns in which rows
        were modified.

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
            other = self.init_with_table(col=self.col, table=self._anki_table)
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
            columns=cols,
        )

    def was_added(self, other: Optional[pd.DataFrame] = None, _force=False):
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
            other_ids = set(other.index)
        else:
            other_ids = set(self.col._get_original_item(self._anki_table).id)

        new_indices = set(self.index) - other_ids
        return self.index.isin(new_indices)

    def was_deleted(
        self, other: Optional[pd.DataFrame] = None, _force=False
    ) -> List:
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
            other_ids = set(other.index)
        else:
            other_ids = set(self.col._get_original_item(self._anki_table).id)

        deleted_indices = other_ids - set(self.index)
        return sorted(list(deleted_indices))

    # Update modification stamps and similar
    # ==========================================================================

    def _set_usn(self):
        """ Update usn (update sequence number) for all changed rows. """
        self.loc[
            self.was_modified(na=True, _force=True),
            _columns.columns_anki2ours[self._anki_table]["usn"],
        ] = -1

    def _set_mod(self):
        """ Update modification timestamps for all changed rows. """
        if self._anki_table in ["cards", "notes"]:
            self.loc[
                self.was_modified(na=True, _force=True),
                _columns.columns_anki2ours[self._anki_table]["mod"],
            ] = int(time.time())

    # todo: test
    def _set_guid(self):
        """ Update globally unique id """
        if self._anki_table == "notes":
            self.loc[~self["nguid"].apply(bool)].apply(generate_guid)

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
            df = self.copy(True)
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

        self.rename(columns=_columns.columns_anki2ours[table], inplace=True)

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

        id_field = _columns.table2index[table]
        duplicate_ids = self[id_field][self[id_field].duplicated()].tolist()
        if duplicate_ids:
            log.critical(
                "The following IDs occur "
                "more than once: {}. Please do not use this dataframe.".format(
                    ", ".join(map(str, duplicate_ids))
                )
            )
        self.set_index(id_field, inplace=True)

        if table == "cards":
            self["cdeck"] = self["did"].map(raw.get_did2deck(self.db))
            self["codeck"] = self["codid"].map(raw.get_did2deck(self.db))
        elif table == "notes":
            self["nmodel"] = self["mid"].map(raw.get_mid2model(self.db))

        # Tags
        # ----

        if table == "notes":
            # Tags as list, rather than string joined by space
            self["ntags"] = self["ntags"].apply(
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

        drop_columns = set(self.columns) - set(_columns.our_columns[table])
        self.drop(drop_columns, axis=1, inplace=True)

        self.check_table_integrity()

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
            df = self.copy(True)
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
            self["did"] = self["cdeck"].map(raw.get_deck2did(self.db))
            self["odid"] = self["codeck"].map(raw.get_deck2did(self.db))
        if table == "notes":
            self["mid"] = self["nmodel"].map(raw.get_model2mid(self.db))

        # Fields & Hashes
        # ---------------

        if table == "notes":
            if not self._fields_format == "list":
                self.fields_as_list(inplace=True, force=True)
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
            columns=invert_dict(_columns.columns_anki2ours[table]), inplace=True
        )
        self.rename(columns={"index": "id"}, inplace=True)

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
        # Todo: warn about dropped columns?

        if len(self) == 0:
            new = pd.DataFrame(columns=_columns.anki_columns[table])
        else:
            new = pd.DataFrame(self[_columns.anki_columns[table]])
        self.drop(self.columns, axis=1, inplace=True)
        for col in new.columns:
            self[col] = new[col]

        self.check_table_integrity()

        self._df_format = "anki"

    # Write
    # ==========================================================================

    def summarize_changes(self, output="print") -> Optional[dict]:
        """ Summarize changes that were made with respect to the table
        as loaded from the database.

        Args:
            output: Output mode: 'print' (default: print)
                or 'dict' (return as dictionary)

        Returns:
            None or dictionary
        """
        as_dict = {
            "n": len(self),
            "n_modified": sum(self.was_modified(na=False)),
            "n_added": sum(self.was_added()),
            "n_deleted": len(self.was_deleted()),
        }
        as_dict["has_changed"] = (
            as_dict["n_modified"] or as_dict["n_added"] or as_dict["n_deleted"]
        )
        if output == "print":
            print("Total rows: {}".format(as_dict["n"]))
            print("Compared to original version:")
            print("Modified rows: {}".format(as_dict["n_modified"]))
            print("Added rows: {}".format(as_dict["n_added"]))
            print("Deleted rows: {}".format(as_dict["n_deleted"]))
        elif output == "dict":
            return as_dict
        else:
            raise ValueError("Invalid output setting: {}".format(output))

    # Append
    # ==========================================================================

    def _get_id(self, others=()) -> int:
        """ Generate ID from timestamp and increment if it is already in use.

        .. warning::

            Do not call repeatedly without adding new IDs to index (might
            produce identical IDs). Rather use :meth:`_get_ids` instead.
        """
        idx = int(1000 * time.time())
        while idx in self.index or idx in others:
            idx += 1
        return idx

    # todo: documentation
    def add_card(
        self,
        nid: int,
        cdeck: str,
        cord: Optional[Union[int, List[int]]] = None,
        cmod: Optional[int] = None,
        cusn: Optional[int] = None,
        cqueue: Optional[str] = None,
        ctype: Optional[str] = None,
        civl: Optional[int] = None,
        cfactor: Optional[int] = None,
        creps: Optional[int] = None,
        clapses: Optional[int] = None,
        cleft: Optional[int] = None,
        cdue: Optional[int] = None,
        inplace=False,
    ):
        """
        Similar to :py:meth:`ankipandas.ankipdf.AnkiDataFrame.add_cards`

        Args:
            nid:
            cdeck:
            cord:
            cmod:
            cusn:
            cqueue:
            ctype:
            civl:
            cfactor:
            creps:
            clapses:
            cleft:
            cdue:
            inplace:

        Returns:

        """
        return self.add_cards(
            nid=[nid],
            cdeck=cdeck,
            cord=cord,
            cmod=cmod,
            cusn=cusn,
            cqueue=cqueue,
            ctype=ctype,
            civl=civl,
            cfactor=cfactor,
            creps=creps,
            clapses=clapses,
            cleft=cleft,
            cdue=cdue,
            inplace=inplace,
        )

    # todo: change order of arguments?
    # fixme: cord will be replaced
    # todo: duplicate cards (same note, same cord)?
    def add_cards(
        self,
        nid: List[int],
        cdeck: Union[str, List[str]],
        cord: Optional[Union[int, List[int]]] = None,
        cmod: Optional[Union[int, List[int]]] = None,
        cusn: Optional[Union[int, List[int]]] = None,
        cqueue: Optional[Union[str, List[str]]] = None,
        ctype: Optional[Union[str, List[str]]] = None,
        civl: Optional[Union[int, List[int]]] = None,
        cfactor: Optional[Union[int, List[int]]] = None,
        creps: Optional[Union[int, List[int]]] = None,
        clapses: Optional[Union[int, List[int]]] = None,
        cleft: Optional[Union[int, List[int]]] = None,
        cdue: Optional[Union[int, List[int]]] = None,
        inplace=False,
    ):
        """
        Add cards belonging to notes of one model.

        Args:
            nid: Note IDs of the notes that you want to add cards for
            cdeck: Name of deck to add cards to as string or list of strings
                (different deck for each nid).
            cord: Number of the template to add cards for as int or list
                thereof. The template corresponds to the reviewing
                direction. If left ``None`` (default), cards for all
                templates will be added.
                It is not possible to specify different cord for different
                nids!
            cmod: List of modification timestamps.
                Will be set automatically if ``None`` (default) and it is
                discouraged to set your own.
            cusn: List of Update Sequence Numbers.
                Will be set automatically (to -1, i.e. needs update)
                if ``None`` (default) and it is
                very discouraged to set your own.
            cqueue: 'sched buried', 'user buried', 'suspended', 'new',
                'learning', 'due', 'in learning' (learning but next rev at
                least a day after the previous review). If ``None`` (default),
                'new' is chosen for all cards. Specify as string or list
                thereof.
            ctype: List of card types ('learning', 'review', 'relearn', 'cram').
                If ``None`` (default) 'learning' is chosen for all.
            civl: The new interval that the card was pushed to after the review.
                Positive values are in days, negative values are in seconds
                (for learning cards).  If ``None`` (default) 0 is chosen for
                all cards.
            cfactor: The new ease factor of the card in permille. If ``None``
                (default) 0 is chosen for all.
            creps: Number of reviews. If ``None`` (default), 0 is chosen for
                all cards.
            clapses: The number of times the card went from a 'was answered
                correctly' to 'was answered incorrectly'. If ``None`` (default),
                0 is chosen for all cards.
            cleft: Of the form ``a*1000+b``, with: ``b`` the number of reps
                left till graduation and ``a`` the number of reps left today.
                If ``None`` (default), 0 is chosen for all cards.
            cdue: Due is used differently for different card types: new:
                note id or random int, due: integer day, relative to the
                collection's creation time, learning: integer timestamp.
                If ``None`` (default), check that we're adding a new card and
                set to note ID.
            inplace: If ``False`` (default), return a new
                :class:`~ankipandas.AnkiDataFrame`, if True, modify in place and
                return new card IDs

        Returns:
            :class:`~ankipandas.AnkiDataFrame` if ``inplace==True``, else
            list of new card IDs

        """
        self._check_our_format()
        if not self._anki_table == "cards":
            raise ValueError("Cards can only be added to cards table!")

        # --- Ord ---

        nid2mid = raw.get_nid2mid(self.db)
        missing_nids = sorted(list(set(nid) - set(nid2mid.keys())))
        if missing_nids:
            raise ValueError(
                "The following note IDs (nid) can't be found in the notes "
                "table: {}. Perhaps you didn't call notes.write() to write "
                "them back into the database?".format(
                    ", ".join(map(str, missing_nids))
                )
            )

        mids = list(set(map(lambda x: nid2mid[x], nid)))
        if len(mids) >= 2:
            raise ValueError(
                "It is only supported to add cards for notes of the same model"
                ", but you're trying to add cards for notes of "
                "models: {}".format(", ".join(map(str, mids)))
            )
        mid = mids[0]

        # fixme: should use function from ankipandas.raw
        available_ords = raw.get_mid2templateords(self.db)[mid]
        if cord is None:
            cord = available_ords
        elif isinstance(cord, int):
            cord = [cord]
        elif is_list_like(cord):
            pass
        else:
            raise ValueError(
                "Unknown type for cord specifiation: {}".format(type(cord))
            )
        not_available = sorted(list(set(cord) - set(available_ords)))
        if not_available:
            raise ValueError(
                "The following templates are not available for notes of "
                "this model: {}".format(", ".join(map(str, not_available)))
            )

        # --- Deck ---

        if isinstance(cdeck, str):
            cdeck = [cdeck] * len(nid)
        elif is_list_like(cdeck):
            if len(cdeck) != len(nid):
                raise ValueError(
                    "Number of decks doesn't match number of "
                    "notes for which cards should be added: {} "
                    "instead of {}.".format(len(cmod), len(nid))
                )
        else:
            raise ValueError("Unknown format for cdeck: {}".format(type(cdeck)))
        unknown_decks = sorted(
            list(set(cdeck) - set(raw.get_did2deck(self.db).values()))
        )
        if unknown_decks:
            raise ValueError(
                "The following decks do not seem to exist: {}".format(
                    ", ".join(unknown_decks)
                )
            )

        # --- Rest ---

        def _handle_input(inpt, name, default, typ, options=None):
            if inpt is None:
                inpt = [default] * len(nid)
            elif is_list_like(inpt):
                if len(inpt) != len(nid):
                    raise ValueError(
                        "Number of {} doesn't match number of "
                        "notes for which cards should be added: {} "
                        "instead of {}.".format(name, len(cmod), len(nid))
                    )
            elif isinstance(inpt, typ):
                inpt = [inpt] * len(nid)
            else:
                raise ValueError(
                    "Invalid type of {} specification: {}".format(
                        name, type(inpt)
                    )
                )
            if options is not None:
                invalid = sorted(list(set(inpt) - set(options)))
                if invalid:
                    raise ValueError(
                        "The following values are no valid "
                        "entries for {}: {}".format(name, ", ".join(invalid))
                    )
            return inpt

        cmod = _handle_input(cmod, "cmod", int(time.time()), int)
        cusn = _handle_input(cusn, "cusn", -1, int)
        cqueue = _handle_input(
            cqueue,
            "cqueue",
            "new",
            str,
            options=[
                "sched buried",
                "user buried",
                "suspended",
                "new",
                "learning",
                "due",
                "in learning",
            ],
        )
        ctype = _handle_input(
            ctype,
            "ctype",
            "learning",
            str,
            options=["learning", "review", "relearn", "cram"],
        )
        civl = _handle_input(civl, "civl", 0, int)
        cfactor = _handle_input(cfactor, "cfactor", 0, int)
        creps = _handle_input(creps, "creps", 0, int)
        clapses = _handle_input(clapses, "clapses", 0, int)
        cleft = _handle_input(cleft, "cleft", 0, int)

        # --- Due ---
        # Careful: Has to come after cqueue is defined!

        if cdue is None:
            if set(cqueue) == {"new"}:
                cdue = nid
            else:
                raise ValueError(
                    "Due date can only be set automatically for cards of type"
                    "/queue 'new', but you have types: {}".format(
                        ", ".join(set(cqueue))
                    )
                )
        elif is_list_like(cdue):
            if len(cdue) != len(nid):
                raise ValueError(
                    "Number of cdue doesn't match number of "
                    "notes for which cards should be added: {} "
                    "instead of {}.".format(len(cmod), len(nid))
                )
        elif isinstance(cdue, int):
            cdue = [cdue] * len(nid)
        else:
            raise ValueError(
                "Invalid type of cdue specification: {}".format(type(cdue))
            )

        # Now we need to decide on contents for EVERY column in the DF
        all_cids = self._get_ids(n=len(nid) * len(cord))
        add = pd.DataFrame(columns=self.columns, index=all_cids)
        for icord, co in enumerate(cord):
            cid = all_cids[icord * len(nid) : (icord + 1) * len(nid)]
            known_columns = {
                "nid": nid,
                "cdeck": cdeck,
                "cord": [co] * len(nid),
                "cdue": cdue,
                "cmod": cmod,
                "cusn": cusn,
                "cqueue": cqueue,
                "ctype": ctype,
                "civl": civl,
                "cfactor": cfactor,
                "creps": creps,
                "clapses": clapses,
                "cleft": cleft,
                "codeck": [""] * len(nid),
                "codue": [0] * len(nid),
            }

            for key, item in known_columns.items():
                add.loc[cid, key] = pd.Series(item, index=cid)

        add = add.astype(
            {
                key: value
                for key, value in _columns.dtype_casts_all.items()
                if key in self.columns
            }
        )

        if not inplace:
            return self.append(add)
        else:
            replace_df_inplace(self, self.append(add))
            return all_cids

    def _get_ids(self, n=1) -> List[int]:
        """ Generate ID from timestamp and increment if it is already in use.

        Args:
            n: Number of IDs to generate
        """
        indices = []
        for i in range(n):
            indices.append(self._get_id(others=indices))
        return indices

    # Todo: If tags single list: Same for all!
    def add_notes(
        self,
        nmodel: str,
        nflds: Union[List[List[str]], Dict[str, List[str]]],
        ntags: List[List[str]] = None,
        nid=None,
        nguid=None,
        nmod=None,
        nusn=None,
        inplace=False,
    ):
        """ Add multiple new notes corresponding to one model.

        Args:
            nmodel: Name of the model (must exist already, check
                :meth:`list_models` for a list of available models)
            nflds: Fields of the note either as list of lists, e.g.
                ``[[field1_note1, ... fieldN_note1], ...,
                [field1_noteM, ... fieldN_noteM]]`` or dictionary
                ``{field name: [field_value1, ..., field_valueM]}`` or list of
                dictionaries: ``[{field_name: field_value for note 1}, ...,
                {field_name: field_value for note N}]``.
                If dictionaries are used: If fields are not present,
                they are filled with empty strings.
            ntags: Tags of the note as list of list of strings:
                ``[[tag1_note1, tag2_note1, ... ], ... [tag_1_noteM, ...]]``.
                If ``None``, no tags will be added.
            nid: List of note IDs. Will be set automatically if ``None``
                (default) and it is discouraged to set your own.
            nguid: List of Globally Unique IDs. Will be set automatically if
                ``None`` (default), and it is discouraged to set your own.
            nmod: List of modification timestamps.
                Will be set automatically if ``None`` (default) and it is
                discouraged to set your own.
            nusn: List of Update Sequence Number.
                Will be set automatically (to -1, i.e. needs update)
                if ``None`` (default) and it is
                very discouraged to set your own.
            inplace: If ``False`` (default), return a new
                :class:`~ankipandas.AnkiDataFrame`, if True, modify in place and
                return new note ID

        Returns:
            :class:`~ankipandas.AnkiDataFrame` if ``inplace==True``, else
            new note ID (int)
        """
        self._check_our_format()
        if not self._anki_table == "notes":
            raise ValueError("Notes can only be added to notes table.")

        # --- Model ---

        model2mid = raw.get_model2mid(self.db)
        if nmodel not in model2mid.keys():
            raise ValueError(
                "No model of with name '{}' exists.".format(nmodel)
            )
        field_keys = raw.get_mid2fields(self.db)[model2mid[nmodel]]

        # --- Fields ---

        if is_list_dict_like(nflds):
            n_notes = len(nflds)
            specified_fields = set(
                flatten_list_list(list(map(lambda d: list(d.keys()), nflds)))
            )
            unknown_fields = sorted(list(specified_fields - set(field_keys)))
            if unknown_fields:
                raise ValueError(
                    "Unknown fields: {}".format(", ".join(unknown_fields))
                )
            field_key2field = {
                key: list(map(lambda d: d.get(key), nflds))
                for key in field_keys
            }
        elif is_list_list_like(nflds):
            n_fields = list(set(map(len, nflds)))
            n_notes = len(nflds)
            if not (len(n_fields) == 1 and n_fields[0] == len(field_keys)):
                raise ValueError(
                    "Wrong number of items for specification of field contents:"
                    " There are {} fields for your model type, but you"
                    " specified {} items.".format(
                        len(field_keys), ", ".join(map(str, n_fields))
                    )
                )
            field_key2field = {
                field_keys[i]: list(map(lambda x: x[i], nflds))
                for i in range(len(field_keys))
            }
        elif is_dict_list_like(nflds):
            lengths = list(set(map(len, nflds.values())))
            if len(lengths) >= 2:
                raise ValueError(
                    "Inconsistent number of "
                    "fields: {}".format(", ".join(map(str, lengths)))
                )
            elif len(lengths) == 0:
                raise ValueError("Are you trying to add zero notes?")
            n_notes = lengths[0]
            field_key2field = copy.deepcopy(nflds)
            for key in field_keys:
                if key not in field_key2field:
                    field_key2field[key] = [""] * n_notes
        else:
            raise ValueError("Unsupported fields specification.")

        # --- Tags ---

        if ntags is not None:
            if len(ntags) != n_notes:
                raise ValueError(
                    "Number of tags doesn't match number of notes to"
                    " be added: {} instead of {}.".format(len(ntags), n_notes)
                )
        else:
            ntags = [[]] * n_notes

        # --- Nids ---

        if nid is not None:
            if len(nid) != n_notes:
                raise ValueError(
                    "Number of note IDs doesn't match number of notes to"
                    " be added: {} instead of {}.".format(len(nid), n_notes)
                )
        else:
            nid = self._get_ids(n=n_notes)

        already_present = sorted(list(set(nid).intersection(set(self.index))))
        if already_present:
            raise ValueError(
                "The following note IDs (nid) are "
                "already present: {}".format(", ".join(map(str, nid)))
            )

        if len(set(nid)) < len(nid):
            raise ValueError("Your note ID specification contains duplicates!")

        # --- Mod ---

        if nmod is not None:
            if len(nmod) != n_notes:
                raise ValueError(
                    "Number of modification dates doesn't match number of "
                    "notes to  be added: {} "
                    "instead of {}.".format(len(nmod), n_notes)
                )
        else:
            nmod = [int(time.time()) for _ in range(n_notes)]

        # --- Guid ---

        if nguid is not None:
            if len(nguid) != n_notes:
                raise ValueError(
                    "Number of globally unique IDs (guid) doesn't match number "
                    "of notes to  be added: {} "
                    "instead of {}.".format(len(nguid), n_notes)
                )
        else:
            nguid = [generate_guid() for _ in range(n_notes)]

        existing_guids = sorted(
            list(set(nguid).intersection(self["nguid"].unique()))
        )
        if existing_guids:
            raise ValueError(
                "The following globally unique IDs (guid) are already"
                " present: {}.".format(", ".join(map(str, existing_guids)))
            )

        # todo: make efficient
        duplicate_guids = sorted(set([g for g in nguid if nguid.count(g) >= 2]))
        if duplicate_guids:
            raise ValueError(
                "The following gloally unique IDs (guid) are not unique: ",
                ", ".join(map(str, duplicate_guids)),
            )

        # --- Usn ---

        if nusn is None:
            nusn = -1
        else:
            if len(nusn) != n_notes:
                raise ValueError(
                    "Number of update sequence numbers (usn) doesn't match"
                    "number of notes to  be added: {} "
                    "instead of {}.".format(len(nusn), n_notes)
                )

        # --- Collect all  ---

        # Now we need to decide on contents for EVERY column in the DF
        known_columns = {
            "nmodel": nmodel,
            "ntags": ntags,
            "nguid": nguid,
            "nmod": nmod,
            "nusn": nusn,
        }

        # More difficult: Field columns:
        if self._fields_format == "list":
            # Be careful with order!
            # Also need to flip dimensions
            known_columns["nflds"] = np.swapaxes(
                [field_key2field[field_key] for field_key in field_keys], 0, 1
            ).tolist()
        elif self._fields_format == "columns":
            # First we need to make sure that the df has the columns for our
            # model (perhaps this is the first note of this model that we're
            # adding, so fields_as_columns() didn't add them).
            for col in field_keys:
                if col not in self:
                    self[self.fields_as_columns_prefix + col] = ""
            # Let's first set all fields as columns to '', because we also
            # need to set those which aren't from our model:
            for col in self.columns:
                if col.startswith(self.fields_as_columns_prefix):
                    known_columns[col] = [""] * n_notes
            # Now let's fill those of our model
            for col, values in field_key2field.items():
                known_columns[self.fields_as_columns_prefix + col] = values
        else:
            raise ValueError(
                "Fields have to be in 'list' or 'columns' format, but yours "
                "are in '{}' format.".format(self._fields_format)
            )

        add = pd.DataFrame(columns=self.columns, index=nid)
        for key, item in known_columns.items():
            add.loc[:, key] = pd.Series(item, index=nid)
        add = add.astype(
            {
                key: value
                for key, value in _columns.dtype_casts_all.items()
                if key in self.columns
            }
        )
        if not inplace:
            return self.append(add)
        else:
            replace_df_inplace(self, self.append(add))
            return nid

    def add_note(
        self,
        nmodel: str,
        nflds: Union[List[str], Dict[str, str]],
        ntags=None,
        nid=None,
        nguid=None,
        nmod=None,
        nusn=-1,
        inplace=False,
    ):
        """ Add new note.

        .. note::

            For better performance it is advisable to use :meth:`add_notes`
            when adding many notes.

        Args:
            nmodel: Name of the model (must exist already, check
                :meth:`list_models` for a list of available models)
            nflds: Fields of the note either as list or as dictionary
                ``{field name: field value}``. In the latter case, if fields
                are not present, they are filled with empty strings.
            ntags: Tags of the note as string or Iterable thereof. Defaults to
                no tags.
            nid: Note ID. Will be set automatically by default and it is
                discouraged to set your own. If you do so and it already
                exists, the existing note will be overwritten.
            nguid: Note Globally Unique ID. Will be set automatically by
                default, and it is discouraged to set your own.
            nmod: Modification timestamp. Will be set automatically by default
                and it is discouraged to set your own.
            nusn: Update sequence number. Will be set automatically
                (to -1, i.e. needs update) if ``None`` (default) and it is
                very discouraged to set your own.
            inplace: If False (default), return a new
                :class:`ankipandas.AnkiDataFrame`, if True, modify in place and
                return new note ID

        Returns:
            :class:`ankipandas.AnkiDataFrame` if ``inplace==True``, else
            new note ID (``int``)

        """
        if is_list_like(nflds):
            nflds = [nflds]
        elif isinstance(nflds, dict):
            nflds = [nflds]
        else:
            raise ValueError(
                "Unknown type for fields specification: {}".format(type(nflds))
            )
        if ntags is not None:
            ntags = [ntags]
        if nid is not None:
            nid = [nid]
        if nguid is not None:
            nguid = [nguid]
        if nmod is not None:
            nmod = [nmod]
        if nusn is not None:
            nusn = [nusn]

        ret = self.add_notes(
            nmodel=nmodel,
            nflds=nflds,
            ntags=ntags,
            nid=nid,
            nguid=nguid,
            nmod=nmod,
            nusn=nusn,
            inplace=inplace,
        )
        if inplace:
            # We get nids back
            return ret[0]
        else:
            # We get new AnkiDataFrame back
            return ret

    # Help
    # ==========================================================================

    # todo: test?
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

    def help_cols(
        self, column="auto", table="all", ankicolumn="all"
    ) -> pd.DataFrame:
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
        if column == "auto":
            column = list(self.columns)
        if table != "all":
            if isinstance(table, str):
                table = [table]
            df = df[df["Table"].isin(table)]
        if column != "all":
            if isinstance(column, str):
                column = [column]
            df = df[df["Column"].isin(column)]
        if ankicolumn != "all":
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
        h = (
            "This is the help for the class AnkiDataFrame, a subclass of "
            "pandas.DataFrame. \n"
            "The full documentation of all class methods "
            "unique to AnkiDataFrame can be found on "
            "https://ankipandas.readthedocs.io. \n"
            "The inherited methods from "
            "pandas.DataFrame are documented at https://pandas.pydata.org/"
            "pandas-docs/stable/reference/api/pandas.DataFrame.html.\n"
            "To get information about the fields currently in this table, "
            "please use the help_cols() method."
        )
        if ret:
            return h
        else:
            print(h)
