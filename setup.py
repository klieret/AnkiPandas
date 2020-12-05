#!/usr/bin/env python3

""" To install this package, change to the directory of this file and run

    pip3 install --user .

(the ``--user`` flag installs the package for your user account only, otherwise
you will need administrator rights).
"""

# std
from distutils.core import setup
import site
import sys

# noinspection PyUnresolvedReferences
import setuptools  # see below (1)
from pathlib import Path

# (1) see https://stackoverflow.com/questions/8295644/
# Without this import, install_requires won't work.

# Sometimes editable install fails with an error message about user site
# being not writeable. The following line can fix that, see
# https://github.com/pypa/pip/issues/7953
site.ENABLE_USER_SITE = "--user" in sys.argv[1:]

keywords = ["anki", "pandas", "dataframe"]

description = (
    "Load your anki database as a pandas DataFrame with just one "
    "line of code!"
)

this_dir = Path(__file__).resolve().parent

packages = setuptools.find_packages()

with (this_dir / "README.md").open(encoding="utf8") as fh:
    long_description = fh.read()

with (this_dir / "ankipandas" / "version.txt").open(encoding="utf8") as vf:
    version = vf.read().strip()

with (this_dir / "requirements.txt").open(encoding="utf8") as rf:
    requirements = [
        req.strip()
        for req in rf.readlines()
        if req.strip() and not req.startswith("#")
    ]


setup(
    name="ankipandas",
    version=version,
    packages=packages,
    url="https://github.com/klieret/ankipandas",
    project_urls={
        "Bug Tracker": "https://github.com/klieret/ankipandas/issues",
        "Documentation": "https://ankipandas.readthedocs.io/",
        "Source Code": "https://github.com/klieret/ankipandas/",
    },
    package_data={"ankipandas": ["anki_fields.csv", "data/*"]},
    install_requires=requirements,
    license="MIT",
    keywords=keywords,
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Database",
        "Topic :: Education",
        "Topic :: Utilities",
    ],
)
