#!/usr/bin/env python3

# std
import unittest

# 3rd
import pandas as pd

# ours
from ankipandas.util.dataframe import replace_df_inplace


class TestUtils(unittest.TestCase):
    def test__replace_df_inplace(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        df_new = pd.DataFrame({"a": [1]})
        replace_df_inplace(df, df_new)
        self.assertEqual(len(df), 1)
        self.assertEqual(len(df.columns), 1)
        self.assertListEqual(list(df["a"].values), [1])


if __name__ == "__main__":
    unittest.main()
