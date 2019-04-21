#!/usr/bin/env python3

# std
import sqlite3

# 3rd
import pandas as pd

# ours
import ankipandas.convenience_functions as convenience
import ankipandas.core_functions as core


# todo: inplace == false as default
class AnkiDataFrame(pd.DataFrame):
    _attributes = ("db", "db_path", "table")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if len(args) == 1 and isinstance(args[0], AnkiDataFrame):
            args[0]._copy_attrs(self)
        self.db = None
        self.db_path = None
        self.table = None

    def _load_db(self, path):
        self.db = core.load_db(path)
        self.db_path = path

    def _get_table(self, path, table):
        if not path:
            path = self.db_path
        self._load_db(path)
        table = core._get_table(self.db, table)
        core._replace_df_inplace(self, table)
        self.table = table

    @property
    def nid_column(self):
        if self.table == "notes":
            return "id"
        else:
            return "nid"

    @property
    def cid_column(self):
        if self.table == "cards":
            return "id"
        else:
            return "cid"

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

    def merge_note_info(self, columns=None, drop_columns=None, prepend="n",
                        prepend_clash_only=True, nid_column="nid"):
        core.merge_note_info(
            db=self.db,
            df=self,
            inplace=True,
            columns=columns,
            drop_columns=drop_columns,
            nid_column=nid_column,
            prepend=prepend,
            prepend_clash_only=prepend_clash_only
        )

    def merge_card_info(self, columns=None, drop_columns=None, prepend="c",
                        prepend_clash_only=True, cid_column="cid"):
        core.merge_card_info(
            db=self.db,
            df=self,
            inplace=True,
            prepend=prepend,
            prepend_clash_only=prepend_clash_only,
            columns=columns,
            drop_columns=drop_columns,
            cid_column=cid_column
        )

    def add_nids(self, cid_column=None):
        if not cid_column:
            cid_column = self.cid_column
        core.add_nids(
            db=self.db,
            df=self,
            inplace=True,
            cid_column=cid_column
        )

    def add_mids(self, nid_column=None):
        if not nid_column:
            nid_column = self.nid_column
        # Todo: Perhaps call add_nids, if nid column not found
        core.add_mids(
            db=self.db,
            df=self,
            inplace=True,
            nid_column=nid_column
        )

    def add_model_names(self, mid_column="mid", new_column="mname"):
        # Todo: Perhaps call add_mids, if nid column not found
        core.add_model_names(
            db=self.db,
            df=self.df,
            inplace=True,
            mid_column=mid_column,
            new_column=new_column
        )

    def add_deck_names(self, new_column="dname", did_column="did"):
        core.add_deck_names(
            self.db,
            self,
            inplace=True,
            did_column=did_column,
            new_column=new_column
        )

    def add_fields_as_columns(self, mid_column="mid", prepend="",
                              flds_column="flds"):
        core.add_fields_as_columns(
            db=self.db,
            df=self,
            inplace=True,
            mid_column=mid_column,
            prepend=prepend,
            flds_column=flds_column
        )

    def fields_as_columns_to_flds(self, mid_column="mid", prepended="",
                                  drop=False):
        core.fields_as_columns_to_flds(
            db=self.db,
            df=self,
            mid_column=mid_column,
            prepended=prepended,
            drop=drop
        )


class Cards(AnkiDataFrame):
    def __init__(self, *args, path=None, **kwargs):
        super().__init__(*args, **kwargs)
        if len(args) == 0 and len(kwargs) == 0 and path:
            self._get_table(path, "cards")


class Notes(AnkiDataFrame):
    def __init__(self, *args, path=None, **kwargs):
        super().__init__(*args, **kwargs)
        if len(args) == 0 and len(kwargs) == 0 and path:
            self._get_table(path, "notes")


class Revlog(AnkiDataFrame):
    def __init__(self, *args, path=None, **kwargs):
        super().__init__(*args, **kwargs)
        if len(args) == 0 and len(kwargs) == 0 and path:
            self._get_table(path, "revlog")
