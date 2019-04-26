AnkiPandas: Open your Anki database as a pandas DataFrame in just one line!
===========================================================================

|Build Status| |Coveralls| |Doc Status| |Pypi status| |Chat| |License|

.. |Build Status| image:: https://travis-ci.org/klieret/AnkiPandas.svg?branch=master
   :target: https://travis-ci.org/klieret/AnkiPandas

.. |Coveralls| image:: https://coveralls.io/repos/github/klieret/AnkiPandas/badge.svg?branch=master
   :target: https://coveralls.io/github/klieret/AnkiPandas?branch=master

.. |Doc Status| image:: https://readthedocs.org/projects/ankipandas/badge/?version=latest
   :target: https://ankipandas.readthedocs.io/
   :alt: Documentation Status

.. |Pypi Status| image:: https://badge.fury.io/py/ankipandas.svg
    :target: https://badge.fury.io/py/ankipandas
    :alt: Pypi status

.. |Chat| image:: https://img.shields.io/gitter/room/ankipandas/community.svg
   :target: https://gitter.im/ankipandas/community
   :alt: Gitter

.. |License| image:: https://img.shields.io/github/license/klieret/ankipandas.svg
   :target: https://github.com/klieret/ankipandas/blob/master/LICENSE.txt
   :alt: License

.. start-body

Description
-----------

With this small python package, you can easily load all of your Anki flashcards
as a all-in-one pandas DataFrame!

**Pros**:

* Use all of your mighty pandas tools to data science the heck out of
  your Anki collection
* Just one line of code to get your data frame containing all the information
  you need
* Bring together information about cards, notes and models in just one object!
  There's no need to go from cards to corresponding notes to corresponding
  note model just to find out the field names and contents.
* Easily manipulate and write back data (experimental)
* Easy installation (does not depend on any anki installation)


Installation
------------

``AnkiPandas`` can be installed with the python package manager:

.. code:: sh

    pip3 install ankipandas

For a local installation, you might want to use the ``--user`` switch of ``pip``.
You can also update your current installation with ``pip3 install --upgrade ankipandas``.

For the latest development version you can also work from a cloned version
of this repository:

.. code:: sh

    git clone https://github.com/klieret/ankipandas/
    cd ankipandas
    pip3 install --user .

Usage
-----

The simplest interface is that of ``AnkiDataFrame`` (a subclass of pandas ``DataFrame``):

It's as easy as this:

.. code:: python

    from ankipandas import AnkiDataFrame

    adf = AnkiDataFrame.cards()

And you have a dataframe containing all cards, with additional methods that make
many things easy. For example:

.. code:: python

    adf.merge_note_info()

merges all columns from the ntoes that correspond to the cards into the
dataframe.

.. code:: python

    adf.add_deck_names()

Adds the deck names to the dataframe (instead of just deck IDs, ``did``).

.. code:: python

    adf.add_fields_as_columns()

Adds all fields from the notes as new columns to the dataframe (instead of being
all merged in one field ``flds`` as by default).

Take a look at the documentation_ to find out more about more about the
available methods!

.. _documentation: https://ankipandas.readthedocs.io/

The basic implementation is done in a functional way, so if you rather work with
standard pandas DataFrames, you can also just use these functions to manipulate
them.
Again, the documentation_ is a good starting point!

Columns
-------

Get information about the fields in the table:

.. code:: python

    ankipandas.table_help()

Most of this information is from the `ankidroid documentation`_.

.. _ankidroid documentation: https://github.com/ankidroid/Anki-Android/wiki/Database-Structure

Common problems
---------------

* Locked database?

License
-------

This software is lienced under the `MIT license`_.

.. _MIT  license: https://github.com/klieret/ankipandas/blob/master/LICENSE.txt

.. end-body

