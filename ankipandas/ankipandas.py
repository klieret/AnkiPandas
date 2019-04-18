#!/usr/bin/env python3

# std
import sqlite3
import json
import pathlib

# 3rd
import pandas as pd


class AnkiPandas(object):
    def __init__(self, path):
        path = pathlib.Path(path)
        if not path.is_file():
            raise FileNotFoundError(
                "Not a file/file not found: {}".format(path)
            )
        # str(path) so that we can also give pathlib.Path objects
        self.db = sqlite3.connect(str(path.resolve()))

    def cards(self, deck_names=True, merge_notes=True, custom_query=None,
              **kwargs):
        if not custom_query:
            query = "SELECT * FROM cards "
        else:
            query = custom_query
        df = pd.read_sql_query(query, self.db)
        if deck_names:
            df["deck_name"] = df["did"].map(self.did2name())
        if merge_notes:
            notes = self.notes(**kwargs)
            col_clash = set(notes.columns) & set(df.columns)
            rename_dict = {
                col: "n_" + col for col in col_clash
            }
            notes.rename(columns=rename_dict, inplace=True)
            df = df.merge(notes, left_on="nid", right_on="n_id")
            df.drop(["n_id"], axis=1)
        return df

    # todo
    def card(self, cid=None, nid=None, mid=None, *kwargs):
        raise NotImplementedError

    def notes(self, expand_fields=True):
        df = pd.read_sql_query("SELECT * FROM notes ", self.db)
        if expand_fields:
            mids = df["mid"].unique()
            for mid in mids:
                df_model = df[df["mid"] == mid]
                fields = df_model["flds"].str.split("\x1f", expand=True)
                for ifield, field in enumerate(self.field_names(mid=mid)):
                    df.loc[df["mid"] == mid, field] = fields[ifield]
            df.drop(["flds"], axis=1)
        return df

    def note(self, nid=None, cid=None):
        if len([x for x in [nid, cid] if x is not None]) != 1:
            raise ValueError(
                "Please specify either nid (note id) or "
                "cid (card id)."
            )

        if nid:
            return pd.read_sql_query(
                "SELECT * FROM notes where id == {}".format(nid),
                self.db
            )
        if cid:
            # todo
            raise NotImplementedError

    def decks(self):
        _df = pd.read_sql_query("SELECT * FROM col ", self.db)
        assert(len(_df) == 1)
        return json.loads(_df["decks"][0])

    def models(self):
        _df = pd.read_sql_query("SELECT * FROM col ", self.db)
        assert(len(_df) == 1)
        return json.loads(_df["models"][0])

    def model(self, mid=None, nid=None, cid=None):
        """

        Args:
            mid:
            nid:
            cid:

        Returns:

        """
        if len([x for x in [mid, nid, cid] if x is not None]) != 1:
            raise ValueError(
                "Please specify either mid (model id), nid (note id) or "
                "cid (card id)."
            )

        if mid:
            pass

        if nid:
            mid = self.note(nid=nid)["mid"][0]

        if cid:
            mid = self.note(cid=cid)["mid"][0]

        return self.models()[str(mid)]

    def did2name(self):
        decks = self.decks()
        return {
            int(key): decks[key]["name"]
            for key in decks
        }

    def fields(self, mid=None, nid=None, cid=None):
        """
        Return the fields based on either mid, nid or cid

        Args:
            mid:
            nid:
            cid:

        Returns:

        """
        m = self.model(mid=mid, nid=nid, cid=cid)
        return m["flds"]

    def field_names(self, *args, **kwargs):
        return [field["name"] for field in self.fields(*args, **kwargs)]

    def close(self):
        # Important, so that database doesn't stay locked...
        self.db.close()

    # Magic methods

    def __del__(self):
        self.close()