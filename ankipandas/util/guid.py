#!/usr/bin/env python3

import random
import string

# Directly copied from anki utils!


# used in ankiweb
def _base62(num, extra=""):
    s = string
    table = s.ascii_letters + s.digits + extra
    buf = ""
    while num:
        num, i = divmod(num, len(table))
        buf = table[i] + buf
    return buf


_base91_extra_chars = "!#$%&()*+,-./:;<=>?@[]^_`{|}~"


def _base91(num):
    # all printable characters minus quotes, backslash and separators
    return _base62(num, _base91_extra_chars)


def _guid64():
    """Return a base91-encoded 64bit random number."""
    return _base91(random.randint(0, 2 ** 64 - 1))


def guid():
    """ Return globally unique ID """
    return _guid64()
