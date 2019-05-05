#!/usr/bin/env python3

# std
import sqlite3
import copy

# 3rd
import pandas as pd
import pathlib

# ours
import ankipandas.convenience_functions as convenience
import ankipandas.core_functions as core
from ankipandas.util.dataframe import replace_df_inplace
from ankipandas.util.docstrings import parse_docstring, format_docstring


def _copy_docstring(other, desc=None):
    """ Use this as a decorator in order to copy the docstring from the
    first argument.
    Drops the ``df`` and ``db`` arguments from the parameter description.

    Args:
        desc: Replace description with this description
    """
    def copy_docstring_decorator(this):
        docs = other.__doc__
        _desc, _args, _ret = parse_docstring(docs)
        if desc:
            _desc = desc
        this.__doc__ = format_docstring(
            _desc, _args, _ret, drop_arg=["df", "db"]
        )
        return this
    return copy_docstring_decorator



class AnkiDataFrame(pd.DataFrame):
    #: Additional attributes of a :class:`AnkiDataFrame` that a normal
    #: :class:`pandas.DataFrame` does not posess. These will be copied in the
    #: constructor.
    _attributes = ("db", "db_path", "_anki_table")

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
        if len(args) == 1 and isinstance(args[0], AnkiDataFrame):
            self._copy_attrs_from(args[0])

        # IMPORTANT: Make sure to add all attributes to the class variable
        # :attr:`._attributes`. Also all of them have to be initialized as None!
        # (see the code where we copy attributes).

        #: Opened Anki database (:class:`sqlite3.Connection`)
        self.db = None  # type: sqlite3.Connection

        #: Path to Anki database that is opened as :attr:`.db`
        self.db_path = None  # type: pathlib.Path

        #: Type of anki table: 'notes', 'cards' or 'revlog'. This corresponds to
        #: the meaning of the ID row.
        self._anki_table = None  # type: str

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
        self.db = core.load_db(path)
        self.db_path = path

    def _get_table(self, path, user, table):
        if not path:
            path = self.db_path
        self._load_db(convenience.db_path_input(path, user=user))
        if table == "notes":
            df = core.get_notes(self.db)
        elif table == "cards":
            df = core.get_cards(self.db)
        elif table == "revlog":
            df = core.get_revs(self.db)
        else:
            raise ValueError("Unsupported table type: '{}'.".format(table))
        replace_df_inplace(self, df)
        self._anki_table = table

    @classmethod
    def _table_constructor(cls, path, user, table):
        new = AnkiDataFrame()
        new._get_table(path, user, table)
        return new

    @classmethod
    def notes(cls, path=None, user=None):
        """ Initialize :class:`AnkiDataFrame` with notes table loaded from Anki
        database.

        Args:
            path: (Search) path to database see :func:`.db_path_input` for more
                information.
            user: Anki user name. See :func:`.db_path_input` for more
                information.

        Example:

        .. code-block:: python

            import ankipandas
            notes = ankipandas.AnkiDataFrame.notes()

        """
        return cls._table_constructor(path, user, "notes")

    @classmethod
    def cards(cls, path=None, user=None):
        """ Initialize :class:`AnkiDataFrame` with cards table loaded from Anki
        database.

        Args:
            path: (Search) path to database see :func:`.db_path_input` for more
                information.
            user: Anki user name. See :func:`.db_path_input` for more
                information.

        Example:

        .. code-block:: python

            import ankipandas
            cards = ankipandas.AnkiDataFrame.cards()

        """
        return cls._table_constructor(path, user, "cards")

    @classmethod
    def revs(cls, path=None, user=None):
        """ Initialize :class:`AnkiDataFrame` with review table loaded from Anki
        database.

        Args:
            path: (Search) path to database see :func:`.db_path_input` for more
                information.
            user: Anki user name. See :func:`.db_path_input` for more
                information.

        Example:

        .. code-block:: python

            import ankipandas
            revs = ankipandas.AnkiDataFrame.revs()

        """
        return cls._table_constructor(path, user, "revlog")

    # Internal helpers
    # ==========================================================================

    @property
    def _nid_column(self):
        if self._anki_table == "notes":
            return "id"
        else:
            return "nid"

    @property
    def _cid_column(self):
        if self._anki_table == "cards":
            return "id"
        else:
            return "cid"

    @property
    def _mid_column(self):
        return "mid"

    # Public methods
    # ==========================================================================

    # todo: test
    @property
    def nid(self):
        if self._nid_column in self.columns:
            return self[self._nid_column]
        else:
            if self._anki_table == "revlog":
                cards = core.get_cards(self.db)
                cid2nid = dict(zip(cards["id"], cards["nid"]))
                return self.cid.map(cid2nid)
            else:
                raise ValueError(
                    "Note IDs unavailable for table of "
                    "type {}!".format(self._anki_table)
                )
    # todo: test
    @property
    def cid(self):
        if self._cid_column in self.columns:
            return self[self._cid_column]
        else:
            raise ValueError(
                    "Note IDs unavailable for table of "
                    "type {}!".format(self._anki_table)
            )

    # todo: test
    @property
    def mid(self):
        if self._cid_column in self.columns:
            return self[self._cid_column]
        else:
            if self._anki_table in ["revlog", "cards"]:
                notes = core.get_notes(self.db)
                nid2mid = dict(zip(notes["id"], notes["mid"]))
                return self.cid.map(nid2mid)
            else:
                raise ValueError(
                    "Note IDs unavailable for table of "
                    "type {}!".format(self._anki_table)
                )

    # todo: test
    @property
    def mname(self):
        if "mname" in self.columns:
            return self["mname"]
        else:
            return self.mid.map(core.get_model_names(self.db))

    # todo: test
    @property
    def dname(self):
        if "dname" in self.columns:
            return self["mname"]
        else:
            return self.cid.map(core.get_deck_names(self.db))

    # todo: use .nids rather than .nid_columns
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
        return core.merge_dfs(
            df=self,
            df_add=core.get_notes(self.db),
            id_df=self._nid_column,
            id_add="nid",
            inplace=inplace,
            prepend=prepend,
            prepend_clash_only=prepend_clash_only,
            columns=columns,
            drop_columns=drop_columns
        )

    # todo: use .cids rather than .cid_columns
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
        return core.merge_dfs(
            df=self,
            df_add=core.get_cards(self.db),
            id_df=self._cid_column,
            inplace=inplace,
            columns=columns,
            drop_columns=drop_columns,
            id_add="cid",
            prepend=prepend,
            prepend_clash_only=prepend_clash_only
        )

    def add_mnames(self, inplace=False):
        """ Add model names to a dataframe that contains model IDs.

        Args:
            format: "name", "id"
            inplace: If False, return new dataframe, else update old one

        Returns:
            New :class:`pandas.DataFrame` if inplace==True, else None
        """
        # todo: add it then?
        if self._mid_column not in self.columns:
            raise ValueError("Could not find model id column 'mid'")
        if inplace:
            self["mname"] = self[self._mid_column].astype(str).map(
                core.get_model_names(self.db)
            )
        else:
            df = self.copy(True)
            df.add_mnames(inplace=True)
            return df

    # todo: add checker
    def add_dnames(self, inplace=False):
        """
        Add deck names to a dataframe that contains deck IDs.

        Args:
            inplace: If False, return new dataframe, else update old one

        Returns:
            New :class:`pandas.DataFrame` if inplace==True, else None
        """
        return core.sync_dnames_did(
            db=self.db,
            df=self,
            inplace=inplace,
            did_column="did",
            dname_column="dname",
            source="dids"
        )

    def add_fields_as_columns(self, inplace=False, prepend=""):
        """
        In the 'notes' table, the field contents of the notes is contained in
        one column ('flds') by default. With this method, this column can be
        split up into a new column for every field.

        Args:
            inplace: If False, return new dataframe, else update old one
            prepend: Prepend string to all new column names

        Returns:
            New :class:`pandas.DataFrame` if inplace==True, else None
        """
        if self._mid_column not in self.columns:
            raise ValueError("Could not find model id column 'mid'.")
        if "flds" not in self.columns:
            raise ValueError(
                "Could not find fields column 'flds'.".format("flds")
            )
        # fixme: What if one field column is one that is already in use?
        if inplace:
            mids = self[self._mid_column].unique()
            for mid in mids:
                df_model = self[self[self._mid_column] == mid]
                fields = df_model["flds"].str.split("\x1f", expand=True)
                for ifield, field in enumerate(core.get_field_names(self.db)[str(mid)]):
                    self.loc[self[self._mid_column] == mid, prepend + field] = fields[ifield]
        else:
            df = self.copy(True)
            df.add_fields_as_columns(inplace=True, prepend=prepend)
            return df

    def fields_as_columns_to_flds(self, inplace=False,
                                  prepended="", drop=False):
        """
        This reverts :py:func:`~ankipandas.core_functions.add_fields_as_columns`,
        all columns that represented field contents are now merged into one column
        'flds'.

        Args:
            inplace: If False, return new dataframe, else update old one
            prepended: Use this, if the name of columns that contained the fields
                had a string prepended to them
            drop: Drop columns that were now merged into the 'flds' column

        Returns:
            New :class:`pandas.DataFrame` if inplace==True, else None
        """
        if self._mid_column not in self.columns:
            raise ValueError("Could not find model id column 'mid'.")
        if inplace:
            mids = self[self._mid_column].unique()
            to_drop = []
            for mid in mids:
                fields = core.get_field_names(self.db)[str(mid)]
                if prepended:
                    fields = [prepended + field for field in fields]
                self.loc[self[self._mid_column] == mid, "flds"] = \
                    pd.Series(self[fields].values.tolist()).str.join("\x1f")
                if drop:
                    # Careful: Do not delete the fields here yet, other models
                    # might still use them
                    to_drop.extend(fields)
            self.drop(to_drop, axis=1, inplace=True)
        else:
            df = self.copy()
            df.fields_as_columns_to_flds(
                inplace=True,
                prepended=prepended,
                drop=drop,
            )
            return df

    # todo: should be default anyhow
    def convert_tags(format="list", inplace=False):
        """ Converts space separated tags to a list.

        Args:
            format: 'list' or 'string'
            inplace: If False, return new dataframe, else update old one

        Returns:
            New :class:`pandas.DataFrame` if inplace==True, else None
        """
        raise NotImplementedError


    def help_cols(self, *args, **kwargs):
        df = convenience.help_cols(*args, **kwargs)
        return df
    help.__doc__ = convenience.help_cols.__doc__


    def help(self):
        # todo
        return ""
