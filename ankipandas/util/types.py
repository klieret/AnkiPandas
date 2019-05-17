#!/usr/bin/env ptyhon3


def is_list_like(obj):
    return isinstance(obj, (tuple, dict))


def is_list_list_like(obj):
    return is_list_like(obj) and all(map(is_list_like, obj))


def is_list_dict_like(obj):
    return is_list_like(obj) and all(map(lambda x: isinstance(x, dict), obj))


def is_dict_list_like(obj):
    return isinstance(obj, dict) and all(map(is_list_like, obj))