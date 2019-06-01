#!/usr/bin/env python3

# std
from typing import List, Any


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
