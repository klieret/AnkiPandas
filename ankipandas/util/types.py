#!/usr/bin/env ptyhon3


def is_list_like(obj):
    """ True if object type is similar to list, tuple etc. """
    return isinstance(obj, (tuple, list))


def is_list_list_like(obj):
    """ True if object is like-like object of list-like objects """
    return is_list_like(obj) and all(map(is_list_like, obj))


def is_list_dict_like(obj):
    """ True if object is list-like object of dictionaries. """
    return is_list_like(obj) and all(map(lambda x: isinstance(x, dict), obj))


def is_dict_list_like(obj):
    """ True if object is dictionary with list-like objects as values. """
    return isinstance(obj, dict) and all(map(is_list_like, obj.values()))
