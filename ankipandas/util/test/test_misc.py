#!/usr/bin/env python3

# std
import unittest

# ours
from ankipandas.util.misc import invert_dict


class TestInvertDict(unittest.TestCase):
    def test_ok(self):
        a = {1: 2, 3: 4, 5: 6}
        self.assertDictEqual(invert_dict(a), {2: 1, 4: 3, 6: 5})

    def test_fails(self):
        a = {1: 2, 3: 2}
        with self.assertRaises(ValueError):
            invert_dict(a)


if __name__ == "__main__":
    unittest.main()
