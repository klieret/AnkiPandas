Analyze and manipulate your Anki collection using pandas!
=========================================================

|Build Status| |Coveralls| |Doc Status| |Pypi package| |Chat| |License|

.. |Build Status| image:: https://travis-ci.org/klieret/AnkiPandas.svg?branch=master
   :target: https://travis-ci.org/klieret/AnkiPandas

.. |Coveralls| image:: https://coveralls.io/repos/github/klieret/AnkiPandas/badge.svg?branch=master
   :target: https://coveralls.io/github/klieret/AnkiPandas?branch=master

.. |Doc Status| image:: https://readthedocs.org/projects/ankipandas/badge/?version=latest
   :target: https://ankipandas.readthedocs.io/
   :alt: Documentation Status

.. |Pypi package| image:: https://badge.fury.io/py/ankipandas.svg
    :target: https://pypi.org/project/ankipandas/
    :alt: Pypi status

.. |Chat| image:: https://img.shields.io/gitter/room/ankipandas/community.svg
   :target: https://gitter.im/ankipandas/community
   :alt: Gitter

.. |License| image:: https://img.shields.io/github/license/klieret/ankipandas.svg
   :target: https://github.com/klieret/ankipandas/blob/master/LICENSE.txt
   :alt: License

.. start-body

**NOTE: THIS PROJECT IS STILL AT AN EARLY DEVELOPMENT VERSION. TRY OUT WITH CARE.**

Description
-----------

.. image:: https://raw.githubusercontent.com/klieret/AnkiPandas/master/misc/logo/logo_github.png

Anki_ is one of the most popular flashcard system for spaced repetition learning,
pandas_ is the most popular python package for data analysis and manipulation.
So what could be better than to bring both together?

.. _anki: https://apps.ankiweb.net/
.. _pandas: https://pandas.pydata.org/
.. _DataFrame: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html

With ``AnkiPandas`` you can use ``pandas`` to easily analyze or manipulate your
Anki flashcards.

That means you can

* **Select**: Easily select arbitrary subsets of your cards, notes or reviews
  (`one of many introductions <https://medium.com/dunder-data/6fcd0170be9c>`_,
  `official documentation <https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html>`_)
* **Visualize**: Use powerful `built in tools`_ or switch to the even more versatile
  `seaborn`_ (statistical analysis) or `matplotlib`_
* **Manipulate**: Apply fast bulk operations to the table (e.g. add tags, change decks, set field contents, suspend cards, ...)
  or iterate over the table and perform these manipulations step by step

.. _built in tools: https://pandas.pydata.org/pandas-docs/stable/user_guide/visualization.html
.. _matplotlib: https://matplotlib.org/
.. _seaborn: https://seaborn.pydata.org/

**Pros**

* Easy installation via python package manager (independent of your Anki installation)
* Just one line of code to get started
* Bring together information about cards_, notes_, models_, decks_ and more in just one table!
* `Fully documented <https://ankipandas.readthedocs.io/>`_

.. _cards: https://apps.ankiweb.net/docs/manual.html#cards
.. _notes: https://apps.ankiweb.net/docs/manual.html#notes-&-fields
.. _models: https://apps.ankiweb.net/docs/manual.html#note-types
.. _decks: https://apps.ankiweb.net/docs/manual.html#decks

Alternatives: If your main goal is to add new cards, models and more, you can also take a
look at the genanki_ project.

.. _genanki: https://github.com/kerrickstaley/genanki

Installation
------------

``AnkiPandas`` is available as `pypi package <https://pypi.org/project/ankipandas/>`_
and can be installed or upgrade with the `python package manager`_:

.. _python package manager: https://pip.pypa.io/en/stable/

.. code:: sh

    pip3 install --user --upgrade ankipandas

For the latest development version you can also work from a cloned version
of this repository:

.. code:: sh

    git clone https://github.com/klieret/ankipandas/
    cd ankipandas
    pip3 install --user --upgrade .

Usage
-----

Starting up is as easy as this:

.. code:: python

    from ankipandas import AnkiDataFrame

    notes = AnkiDataFrame.notes()

And you have a dataframe containing all notes, with additional methods that make
many things easy.
Similarly, you can load cards or reviews using ``cards()`` or ``revs()``.
If called without any argument ``notes()`` (and friends) tries to find
your Anki database by itself. However this might take some time.
To make it easier, simply supply (part of) the path to the database and (if you have
more than one user) your Anki user name, e.g.
``AnkiDataFrame.cards(".local/share/Anki2/", user="User 1")`` on many Linux
installations.

To get information about the interpretation of each column, use ``notes.help_cols()``.

Take a look at the documentation_ to find out more about more about the
available methods!

.. _documentation: https://ankipandas.readthedocs.io/

Some basic examples:

Analysis
~~~~~~~~

Show a histogram of the number of reviews (repetitions) of each card for all decks:

.. code:: python

    cards = AnkiDataFrame.cards()
    cards.hist(column="creps", by="cdeck")

Show the number of leeches per deck as pie chart:

.. code:: python

    cards = AnkiDataFrame.cards()
    selection = cards[cards.has_tag("leech")]
    selection["cdeck"].value_counts().plot.pie()

Find all notes of model ``MnemoticModel`` with empty ``Mnemotic`` field:

.. code:: python

    notes = AnkiDataFrame.notes().fields_as_columns()
    notes.query("model=='MnemoticModel' and 'Mnemotic'==''")

Manipulations
~~~~~~~~~~~~~

Add the ``difficult-japanese`` and ``marked`` tag to all notes that contain the tags
``Japanese`` and ``leech``:

.. code:: python

    notes = AnkiDataFrame.notes()
    selection = notes.has_tags(["Japanese", "leech"])
    selection = selection.add_tag(["difficult-japanese", "marked"])
    notes.update(selection)
    notes.write()  # Overwrites your database after creating a backup!

Set the ``language`` field to ``English`` for all notes of model ``LanguageModel`` that are tagged with ``English``:

.. code:: python

    notes = AnkiDataFrame.notes()
    selection = notes.has_tag(["English"]).query("model=='LanguageModel'").fields_as_columns()
    selection["language"] = "English"
    notes.update(selection).write()

Move all cards tagged ``leech`` to the deck ``Leeches Only``:

.. code:: python

    cards = AnkiDataFrame.cards().merge_notes()
    selection = cards.has_tag("leech")
    selection["cdeck"] = "Leeches Only"
    cards.update(selection).write()

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


License & Disclaimer
--------------------

This software is licenced under the `MIT license`_ and (despite best testing efforts)
comes **without any warranty**.
The logo is inspired by the `Anki logo`_ (`license <https://github.com/dae/anki/blob/master/LICENSE.logo>`_)
and the `logo of the pandas package`_
(`license2 <https://github.com/pandas-dev/pandas/blob/master/LICENSE>`_).
This library and its author(s) are not affiliated/associated with the main
Anki or pandas project in any way.

.. _MIT license: https://github.com/klieret/ankipandas/blob/master/LICENSE.txt

.. _logo of the pandas package: https://github.com/pandas-dev/pandas/blob/master/doc/logo/pandas_logo.svg
.. _Anki logo: https://github.com/dae/anki/blob/master/web/imgs/anki-logo-thin.png

.. end-body
