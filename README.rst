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

**NOTE: THIS PROJECT IS STILL AT AN EARLY DEVELOPMENT VERSION. TRY OUT WITH CARE AND EXPECT INTERFACE CHANGES.**

**CURRENT STATUS**: Most read access is working and tested. Write access will be
added soon.

Description
-----------

Analyze and manipulate your Anki_ flashcards as a pandas_ DataFrame_!

.. _anki: https://apps.ankiweb.net/
.. _pandas: https://pandas.pydata.org/
.. _DataFrame: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html

**Pros**:

* Use pandas to easily analyze or manipulate your Anki collection
* Just one line of code to get started
* Bring together information about cards_, notes_, models_, decks_ in just one table!
* Easy installation (independent from your anki installation)

.. _cards: https://apps.ankiweb.net/docs/manual.html#cards
.. _notes: https://apps.ankiweb.net/docs/manual.html#notes-&-fields
.. _models: https://apps.ankiweb.net/docs/manual.html#note-types
.. _decks: https://apps.ankiweb.net/docs/manual.html#decks

If your main goal is to add new cards, models and more, you can also take a
look at the genanki_ project alternatively.

.. _genanki: https://github.com/kerrickstaley/genanki

Installation
------------

``AnkiPandas`` can be installed with the `python package manager`_:

.. _python package manager: https://pip.pypa.io/en/stable/

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

The simplest interface is that of an ``AnkiDataFrame`` (a subclass of pandas ``DataFrame``):

It's as easy as this:

.. code:: python

    from ankipandas import AnkiDataFrame

    cards = AnkiDataFrame.cards()

And you have a dataframe containing all cards, with additional methods that make
many things easy.
If called without any argument ``AnkiDataFrame.cards()`` tries to find the location
of your Anki database by itself. However this might take some time.
To make it easier, simply supply (part of) the path to the database and (if you have
more than one user) your Anki user name, e.g.
``AnkiDataFrame.cards(".local/share/Anki2/", user="User 1")`` on many Linux
installations.

For example:

.. code:: python

    # For each card, merge all information from the corresponding note into
    # the dataframe
    cards.merge_notes(inplace=True)

    # Add all fields from the notes as new columns to the dataframe (instead of
    # being merged in one field ``flds`` as by default):
    cards.fields_as_columns(inplace=True)

Take a look at the documentation_ to find out more about more about the
available methods!

.. _documentation: https://ankipandas.readthedocs.io/


Columns
-------

Get information about the columns in the table:

.. code:: python

    cards.help()

Most of this information is from the `ankidroid documentation`_.

.. _ankidroid documentation: https://github.com/ankidroid/Anki-Android/wiki/Database-Structure

Troubleshooting
---------------

See the `troubleshooting section in the documentation`_.

.. _troubleshooting section in the documentation: https://ankipandas.readthedocs.io/en/latest/troubleshooting.html

Contributing
------------

Your help is greatly appreciated! Suggestions, bug reports and feature requests
are best opened as `github issues`_. You could also first discuss in the
`gitter community`_.
If you want to code something yourself, you are very welcome to submit a `pull request`_!

.. _github issues: https://github.com/klieret/ankipandas/issues
.. _gitter community: https://gitter.im/ankipandas/community
.. _pull request: https://github.com/klieret/AnkiPandas/pulls


License
-------

This software is licenced under the `MIT license`_.

.. _MIT license: https://github.com/klieret/ankipandas/blob/master/LICENSE.txt

.. end-body
