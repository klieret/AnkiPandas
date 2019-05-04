#!/usr/bin/env python3


def invert_dict(dct):
    if not len(set(dct.values())) == len(dct.values()):
        raise ValueError(
            "Dictionary does not seem to be invertible."
        )
    return {
        value: key for key, value in dct.items()
    }
