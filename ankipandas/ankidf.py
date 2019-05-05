#!/usr/bin/env python3

# std
import sqlite3

# 3rd
import pandas as pd
import pathlib

# ours
import ankipandas.convenience_functions as convenience
import ankipandas.core_functions as core
from ankipandas.util.dataframe import replace_df_inplace
from ankipandas.columns import columns_anki2ours, our_columns
from ankipandas.util.misc import invert_dict


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

        #: Prefix for fields as columns
        self.fields_as_columns_prefix = "fld_"

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

        # Note: Conversion of dtypes happens first ==> use original
        # column names!
        # todo: this needs to be saved in columns.py
        if table == "notes":
            dtypes = {"id": str, "mid": str}
        elif table == "cards":
            dtypes = {"id": str, "nid": str, "did": str}
        elif table == "revs":
            dtypes = {"id": str, "cid": str}
        else:
            raise ValueError("Invalid table name: {}.".format(table))

        df = core.get_table(self.db, table)
        df = df.astype(dtypes)  # type: pd.DataFrame
        df.rename(columns=columns_anki2ours[table], inplace=True)

        if table == "notes":
            # Tags as list, rather than string joined by space
            df["ntags"] = \
                df["ntags"].apply(
                    lambda joined: [item for item in joined.split(" ") if item]
                )
            # Fields as list, rather than as string joined by \x1f
            df["nflds"] = df["nflds"].str.split("\x1f")

            # Model field
            df["nmodel"] = df["mid"].map(core.get_model_names(self.db))

        if table == "cards":
            # Deck field
            df["cdeck"] = df["did"].map(core.get_deck_names(self.db))

        drop_columns = set(df.columns) - set(our_columns[table])
        for drop_column in drop_columns:
            df.drop(drop_column, axis=1, inplace=True)

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
        return cls._table_constructor(path, user, "revs")

    # ==========================================================================

    def _invalid_table(self):
        raise ValueError("Invalid table: {}.".format(self._anki_table))

    # IDs
    # ==========================================================================

    # todo: call nidS etc. to avoid clashes with attributes?

    @property
    def nid(self):
        if self._anki_table in ["notes", "cards"]:
            if "nid" not in self.columns:
                raise ValueError(
                    "You seem to have removed the 'nid' column. That was not "
                    "a good idea. Cannot get note ID anymore."
                )
            else:
                return self["nid"]
        elif self._anki_table == "revs":
            return self.cid.map(core.cid2nid(self.db))
        else:
            self._invalid_table()

    @property
    def cid(self):
        if self._anki_table in ["cards", "revs"]:
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

    @property
    def mid(self):
        if self._anki_table in ["notes"]:
            if "nmodel" not in self.columns:
                raise ValueError(
                    "You seem to have removed the 'nmodel' column. That was not"
                    " a good idea. Cannot get model ID anymore."
                )
            else:
                return self["nmodel"].map(
                    invert_dict(core.get_model_names(self.db))
                )
        if self._anki_table in ["revs", "cards"]:
            if "nmodel" in self.columns:
                return self["nmodel"].map(
                    invert_dict(core.get_model_names(self.db))
                )
            else:
                return self.nid.map(core.nid2mid(self.db))
        else:
            self._invalid_table()

    @property
    def did(self):
        if self._anki_table == "cards":
            if "cdeck" not in self.columns:
                raise ValueError(
                    "You seem to have removed the 'cdeck' column. That was not "
                    "a good idea. Cannot get deck ID anymore."
                )
            return self["cdeck"].map(invert_dict(core.get_deck_names(self.db)))
        elif self._anki_table == "notes":
            raise ValueError(
                "Notes can belong to multiple decks. Therefore it is impossible"
                " to associate a deck ID with them."
            )
        elif self._anki_table == "revs":
            return self.cid.map(core.cid2did(self.db))
        else:
            self._invalid_table()

    # Merge tables
    # ==========================================================================

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
            df_add=AnkiDataFrame.notes(self.db_path),
            id_df="nid",
            id_add="nid",
            inplace=inplace,
            prepend=prepend,
            prepend_clash_only=prepend_clash_only,
            columns=columns,
            drop_columns=drop_columns
        )

    # todo: support merging into notes frame
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
        if "nflds" not in self.columns:
            raise ValueError(
                "Could not find fields column 'nflds'."
            )
        # fixme: What if one field column is one that is already in use?
        prefix = self.fields_as_columns_prefix
        if inplace:
            mids = self.mid.unique()
            for mid in mids:
                df_model = self[self.mid == mid]
                fields = pd.DataFrame(df_model["nflds"].tolist())
                field_names = core.get_field_names(self.db)[str(mid)]
                for field in field_names:
                    if prefix + field not in self.columns:
                        self[prefix + field] = ""
                for ifield, field in enumerate(field_names):
                    self.loc[self.mid == mid, [prefix + field]] = \
                        fields[ifield].tolist()
            self.drop("nflds", axis=1, inplace=True)
        else:
            df = self.copy(True)
            df.fields_as_columns(inplace=True)
            return df

    def fields_as_list(self, inplace=False):
        """
        This reverts :meth:`.fields_as_columns`, all columns that represented
        field contents are now merged into one column 'nflds'.

        Args:
            inplace: If False, return new dataframe, else update old one

        Returns:
            New :class:`AnkiDataFrame` if inplace==True, else None
        """
        if inplace:
            mids = self.mid.unique()
            to_drop = []
            for mid in mids:
                fields = core.get_field_names(self.db)[str(mid)]
                fields = [
                    self.fields_as_columns_prefix + field for field in fields
                ]
                print(mid, fields)
                print(self[fields])
                print(pd.Series(self[fields].values.tolist()))
                self.loc[self.mid == mid, "nflds"] = \
                    pd.Series(self[fields].values.tolist())
                # Careful: Do not delete the fields here yet, other models
                # might still use them
                to_drop.extend(fields)
            self.drop(to_drop, axis=1, inplace=True)
        else:
            df = self.copy()  # deep?
            df.fields_as_list(
                inplace=True,
            )
            return df

    # Quick access
    # ==========================================================================

    def _check_tag_col(self):
        if "ntags" not in self.columns:
            raise ValueError(
                "Tag column 'ntags' doesn't exist. Perhaps you forgot to merge "
                "the notes into your table?"
            )

    def has_tag(self, tags=None):
        """ Checks whether row has a certain tag ('ntags' column).

        Args:
            tags: String or list thereof. In the latter case, True is returned
                if the row contains any of the specified tags.
                If None (default), True is returned if the row has any tag at
                all.

        Returns:
            Boolean :class:`pd.Series`
        """
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
        """
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
            self["ntags"] = pd.Series([[]]*len(self))


    # Help
    # ==========================================================================

    def help_cols(self, column='auto', table='all', ankicolumn='all') \
            -> pd.DataFrame:
        """
        Return a pandas dataframe containing descriptions of every field in the
        anki database. The arguments below help to filter it.

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

        return df

    def help(self):
        # todo
        return ""
