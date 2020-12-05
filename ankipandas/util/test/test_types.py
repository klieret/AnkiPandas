#!/usr/bin/env python3

# std
import unittest

# ours
from ankipandas.util.types import (
    is_list_like,
    is_list_dict_like,
    is_dict_list_like,
    is_list_list_like,
)
from ankipandas.util.log import set_debug_log_level


class TestTypes(unittest.TestCase):
    def setUp(self):
        set_debug_log_level()

    def test_is_list_like(self):
        self.assertTrue(is_list_like([1, 2]))
        self.assertTrue(is_list_like((1, 2)))
        self.assertFalse(is_list_like("asdf"))

    def test_is_list_list_like(self):
        self.assertTrue(is_list_list_like([[1, 2]]))
        self.assertTrue(is_list_list_like([(1, 2)]))
        self.assertFalse(is_list_list_like([(1, 2), 3]))

    def test_is_list_dict_like(self):
        self.assertTrue(is_list_dict_like([{1: 3}, {4: 5}]))
        self.assertTrue(is_list_dict_like([]))
        self.assertFalse(is_list_dict_like([(1, 2), (4, 5)]))

    def test_is_dict_list_like(self):
        self.assertTrue(is_dict_list_like({1: [], 2: (3, 4)}))
        self.assertTrue(is_dict_list_like({}))
        self.assertFalse(is_dict_list_like([(1, 2), (4, 5)]))


if __name__ == "__main__":
    unittest.main()
