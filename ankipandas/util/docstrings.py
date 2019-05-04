#!/usr/bin/env python3

# std
import collections
from typing import Dict, Tuple


def parse_docstring(string: str) -> Tuple[str, Dict[str, str], str]:
    """ Parses google style docstring.

    Args:
        string: docstring

    Returns: Description [str], description of arguments [Dict[str, str]],
        description of return value [str]

    .. warning::

        Experimental. This is not yet well tested but for this very module.

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
            if len(kv) >= 2:
                _arg = kv[0]
                args[_arg] = ":".join(kv[1:])
            else:
                args[_arg] += kv[0]
        else:
            raise AssertionError
    return desc, args, returns


def format_docstring(desc: str, args: Dict[str, str], returns: str,
                     drop_arg=()) -> str:
    """ Format google style docstring.

    Args:
        desc: Description [str]
        args: Description of parameters Dict[str, str],
        returns: Description of return values
        drop_arg: Remove the following parameters from the description of
            parameters

    Returns:
        Docstring with the info supplied in the parameters.

    .. warning::

        Experimental. This is not yet well tested but for this very module.

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
    ret += returns
    return ret
