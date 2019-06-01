#!/usr/bin/env python3

# std
import unittest

# ours
from ankipandas.util.log import log, get_logger, set_log_level


class TestLogging(unittest.TestCase):
    """ Only tests that things run without error. """

    def test_log(self):
        log.info("Test info")
        log.warning("Test warning")

    def test_get_logger(self):
        get_logger().info("Test info")
        get_logger().warning("Test warning")

    def test_set_log_level(self):
        set_log_level("warning")
        set_log_level("WARNING")
        set_log_level(0)


if __name__ == "__main__":
    unittest.main()
