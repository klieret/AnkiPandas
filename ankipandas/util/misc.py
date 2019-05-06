#!/usr/bin/env python3


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
        raise ValueError(
            "Dictionary does not seem to be invertible."
        )
    return {
        value: key for key, value in dct.items()
    }
