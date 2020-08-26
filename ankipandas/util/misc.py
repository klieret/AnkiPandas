#!/usr/bin/env python3

# std
from typing import List, Any
import collections


def invert_dict(dct: dict) -> dict:
    """ Invert dictionary, i.e. reverse keys and values.

    Args:
        dct: Dictionary

    Returns:
        Dictionary with reversed keys and values.

    Raises:
        :class:`ValueError` if values are not unique.
    """
    if not len(set(dct.values())) == len(dct.values()):
        print(dct)
        print(sorted(list(dct.values())))
        raise ValueError("Dictionary does not seem to be invertible.")
    return {value: key for key, value in dct.items()}


def flatten_list_list(lst: List[List[Any]]) -> List[Any]:
    """ Takes a list of lists and returns a list of all elements.

    Args:
        lst: List of Lists

    Returns:
        list
    """
    return [item for sublist in lst for item in sublist]


def nested_dict():
    """ This is very clever and stolen from
    https://stackoverflow.com/questions/16724788/
    Use it to initialize a dictionary-like object which automatically adds
    levels.
    E.g.

    .. code-block:: python

        a = nested_dict()
        a['test']['this']['is']['working'] = "yaaay"
    """
    return collections.defaultdict(nested_dict)


def defaultdict2dict(defdict: collections.defaultdict):
    return {
        key: defaultdict2dict(value)
        if isinstance(value, collections.defaultdict)
        else value
        for key, value in defdict.items()
    }
