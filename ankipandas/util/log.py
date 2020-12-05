#!/usr/bin/env python3

# std
import colorlog
import logging
from typing import Union


LOG_DEFAULT_LEVEL = logging.INFO


def get_logger():
    """ Sets up global logger. """
    _log = colorlog.getLogger("AnkiPandas")

    if _log.handlers:
        # the logger already has handlers attached to it, even though
        # we didn't add it ==> logging.get_logger got us an existing
        # logger ==> we don't need to do anything
        return _log

    _log.setLevel(LOG_DEFAULT_LEVEL)

    sh = colorlog.StreamHandler()
    log_colors = {
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red",
    }
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)s: %(message)s", log_colors=log_colors
    )
    sh.setFormatter(formatter)
    # Controlled by overall logger level
    sh.setLevel(logging.DEBUG)

    _log.addHandler(sh)

    return _log


def set_log_level(level: Union[str, int]) -> None:
    """ Set global log level.

    Args:
        level: Either an int
            (https://docs.python.org/3/library/logging.html#levels)
            or one of the keywords, 'critical' (only the most terrifying of log
            messages), 'error', 'warning', 'info',
            'debug' (all log messages)

    Returns:
        None
    """
    lvl = level
    if isinstance(level, str):
        lvl = getattr(logging, level.upper())
    get_logger().setLevel(lvl)


def set_debug_log_level() -> None:
    """ Set global log level to debug. """
    set_log_level(logging.DEBUG)


log = get_logger()
