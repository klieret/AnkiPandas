#!/usr/bin/env python3

import collections


def parse_docstring(string):
    """ Parses docstring

    Args:
        string: docstring

    Returns: Description [str], description of arguments [Dict[str, str]],
        description of return value [str]
    """
    if not string:
        return "", {}, ""
    desc = ""
    args = collections.OrderedDict({})
    returns = ""
    _section = "desc"
    _arg = None
    for line in string.split("\n"):
        if "Args:" in line or "Arguments:" in line:
            _section = "args"
            continue
        if "Returns:" in line:
            _section = "returns"
            continue
        if _section == "desc":
            desc += line + "\n"
        elif _section == "returns":
            returns += line + "\n"
        elif _section == "args":
            kv = line.split(":")
            if len(kv) == 2:
                _arg = kv[0]
                args[_arg] = kv[1]
            else:
                args[_arg] += kv[0].strip()
        else:
            raise AssertionError
    return desc, args, returns


def format_docstring(desc, args, returns, drop_arg=()):
    """ Format docstring.

    Args:
        desc: Description [str]
        args: Description of parameters Dict[str, str],
        returns: Description of return values
        drop_arg: Remove the following parameters from the description of
            parameters

    Returns:
        Docstring with the info supplied in the parameters.
    """
    ret = desc
    ret += "\n\nArgs:\n"
    skip = False
    for arg, argdesc in args.items():
        for da in drop_arg:
            if da.strip().lower() == arg.strip().lower():
                skip = True
                break
        if skip:
            skip = False
            continue
        ret += "{}: {}\n".format(arg, argdesc)
    ret += "\nReturns:\n"
    ret += returns.strip()
    return ret
