#!/usr/bin/env python3

# std
from distutils.core import setup
# noinspection PyUnresolvedReferences
import setuptools  # see below (1)
from pathlib import Path

# (1) see https://stackoverflow.com/questions/8295644/
# Without this import, install_requires won't work.


keywords = [
    "anki",
    "pandas",
]

description = "Load your anki database as a pandas DataFrame with just one " \
              "line of code!"

this_dir = Path(__file__).resolve().parent

packages = setuptools.find_packages()

with (this_dir / "README.rst").open() as fh:
    long_description = fh.read()

with (this_dir / "ankipandas" / "version.txt").open() as vf:
    version = vf.read()

setup(
    name='ankipandas',
    version=version,
    packages=packages,
    url="https://github.com/klieret/ankipandas",
    project_urls={
        "Bug Tracker": "https://github.com/klieret/ankipandas/issues",
        "Documentation": "https://ankipandas.readthedocs.io/",
        "Source Code": "https://github.com/klieret/ankipandas/",
    },
    package_data={
        'ankipandas': ['anki_fields.csv', 'version.txt'],
    },
    install_requires=["pandas"],
    license="MIT",
    keywords=keywords,
    description=description,
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Database",
        "Topic :: Education",
        "Topic :: Utilities"
    ],
)
