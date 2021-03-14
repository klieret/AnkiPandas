#!/usr/bin/env python3

# std
import os
from pathlib import Path
import sys
import logging

# 3rd
import matplotlib.pyplot as plt

# ours
sys.path.insert(0, "../..")
import ankipandas  # noqa E402
from ankipandas.util.log import get_logger  # noqa E402


class Loader(object):
    def __init__(self):
        this_dir = Path(__file__).parent
        self.col_path = this_dir / "col.anki2"
        self.examples_dir = this_dir / "examples"
        self.output_dir = this_dir / "plots"
        self.log = get_logger()
        self.log.setLevel(logging.DEBUG)

    def get_examples(self):
        examples = []
        for root, dirs, files in os.walk(str(self.examples_dir)):
            for file in files:
                examples.append(Path(root) / file)
        return examples

    def run_example(self, path: Path, save=True):
        self.log.info("Running example {}".format(path))
        col = ankipandas.Collection(self.col_path)  # noqa F841
        with path.open("r") as example_file:
            exec(example_file.read())
        if save:
            out = self.output_dir.resolve() / (path.resolve().stem + ".png")
            self.log.info("Plotting to {}".format(out))
            plt.savefig(out, bbox_inches="tight", transparent=True, dpi=75)
            plt.cla()
            plt.clf()
            plt.close()

    def run_all(self, **kwargs):
        for example in self.get_examples():
            self.run_example(example, **kwargs)


if __name__ == "__main__":
    loader = Loader()
    loader.run_all()
