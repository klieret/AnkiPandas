#!/usr/bin/env python3

# std

# 3rd
import pandas as pd

# ours
import ankipandas.convenience_functions as convenience
import ankipandas.core_functions as core
from ankipandas.docstring_utils import *


def _adapt_docstring(method, replace_desc=None):
    docs = method.__doc__
    desc, args, ret = parse_docstring(docs)
    if replace_desc:
        desc = replace_desc
    return format_docstring(desc, args, ret, drop_arg=["df", "db"])


class AnkiDataFrame(pd.DataFrame):
    _attributes = ("db", "db_path", "_anki_table")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(args) == 1 and isinstance(args[0], AnkiDataFrame):
            args[0]._copy_attrs(self)
        self.db = None
        self.db_path = None
        self._anki_table = None

    @property
    def _constructor(self):
        def __constructor(*args, **kw):
            df = self.__class__(*args, **kw)
            self._copy_attrs(df)
            return df
        return __constructor

    def _copy_attrs(self, df):
        for attr in self._attributes:
            df.__dict__[attr] = getattr(self, attr, None)

    # Constructors
    # ==========================================================================

    def _load_db(self, path):
        self.db = core.load_db(path)
        self.db_path = path

    def _get_table(self, path, table):
        if not path:
            path = self.db_path
        if not path:
            path = convenience.find_database()
        self._load_db(path)
        df = core._get_table(self.db, table)
        core._replace_df_inplace(self, df)
        self._anki_table = table

    @classmethod
    def _table_constructor(cls, path, table):
        new = AnkiDataFrame()
        new._get_table(path, table)
        return new

    @classmethod
    def notes(cls, path):
        """ Initialize AnkiDataFrame with notes table loaded from Anki
        database. """
        return cls._table_constructor(path, "notes")

    @classmethod
    def cards(cls, path):
        """ Initialize AnkiDataFrame with cards table loaded from Anki
        database. """
        return cls._table_constructor(path, "cards")

    @classmethod
    def revlog(cls, path):
        """ Initialize AnkiDataFrame with revlog table loaded from Anki
        database. """
        return cls._table_constructor(path, "revlog")

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

    # Public methods
    # ==========================================================================

    def merge_note_info(self, *args, **kwargs):
        return core.merge_note_info(
            db=self.db,
            df=self,
            *args,
            **kwargs
        )
    merge_note_info.__doc__ = _adapt_docstring(core.merge_note_info)

    def merge_card_info(self, *args, **kwargs):
        return core.merge_card_info(
            db=self.db,
            df=self,
            *args,
            **kwargs
        )
    merge_card_info.__doc__ = _adapt_docstring(core.merge_card_info)

    def add_nids(self, cid_column=None, *args, **kwargs):
        if not cid_column:
            cid_column = self._cid_column
        return core.add_nids(
            db=self.db,
            df=self,
            cid_column=cid_column,
            *args,
            **kwargs
        )
    add_nids.__doc__ = _adapt_docstring(
        core.add_nids,
        "Add note IDs"
    )

    def add_mids(self, nid_column=None, *args, **kwargs):
        if not nid_column:
            nid_column = self._nid_column
        # Todo: Perhaps call add_nids, if nid column not found
        return core.add_mids(
            db=self.db,
            df=self,
            nid_column = nid_column,
            *args,
            **kwargs
        )
    add_mids.__doc__ = _adapt_docstring(
        core.add_mids,
        "Add model IDs"
    )

    def add_model_names(self, *args, **kwargs):
        # Todo: Perhaps call add_mids, if nid column not found
        return core.add_model_names(
            db=self.db,
            df=self,
            *args,
            **kwargs
        )
    add_model_names.__doc__ = _adapt_docstring(core.add_model_names)

    def add_deck_names(self, *args, **kwargs):
        return core.add_deck_names(
            self.db,
            self,
            *args,
            **kwargs
        )
    add_deck_names.__doc__ = _adapt_docstring(core.add_deck_names)

    def add_fields_as_columns(self, *args, **kwargs):
        return core.add_fields_as_columns(
            db=self.db,
            df=self,
            *args,
            **kwargs
        )
    add_fields_as_columns.__doc__ = _adapt_docstring(core.add_fields_as_columns)

    def fields_as_columns_to_flds(self, *args, **kwargs):
        return core.fields_as_columns_to_flds(
            db=self.db,
            df=self,
            *args,
            **kwargs
        )
    fields_as_columns_to_flds.__doc__ = \
        _adapt_docstring(core.fields_as_columns_to_flds)

    def help(self, columns=None):
        """ Print help about all known columns in this AnkiDataFrame. """
        if not columns:
            columns = list(self.columns)
        df = convenience.table_help(columns=columns)
        return df

    # def write(self):
    #