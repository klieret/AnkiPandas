AnkiPandas: Open your Anki database as a pandas DataFrame in just one line!
===========================================================================

|Build Status| |Coveralls| |Doc Status| |Pypi status| |Chat| |License|

.. |Build Status| image:: https://travis-ci.org/klieret/ankipandas.svg?branch=master
   :target: https://travis-ci.org/clusterking/clusterking

.. |Coveralls| image:: https://coveralls.io/repos/github/klieret/ankipandas/badge.svg?branch=master
   :target: https://coveralls.io/github/clusterking/clusterking?branch=master

.. |Doc Status| image:: https://readthedocs.org/projects/ankipandas/badge/?version=latest
   :target: https://ankipandas.readthedocs.io/
   :alt: Documentation Status

.. |Pypi Status| image:: https://badge.fury.io/py/clusterking.svg
    :target: https://badge.fury.io/py/clusterking
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
* Easy installation (does not depend on any anki installation)

**Cons**:

* This package does not aim to write back to your database (yet)

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

It's as easy as this:

.. code:: python

    import ankipandas

    ankipandas.load_cards()

And you have a dataframe containing all cards (with all the information from the
notes, such as all the fields already added to it).

Take a look at the documentation_ to find out more about the parameters.

.. _documentation: https://ankipandas.readthedocs.io/

Similarly there are the functions ``load_notes()`` (just load notes) and
``load_reflog()`` (to load the dataframe that contains information about
every review that was ever done). Again, these can be tweaked with parameters,
but by default include as much information as possible in one dataframe.

If you want to fine-tweak this, take a look at the core functions, which are
slightly more low-level, but allow you to get to your dataframe step by step.

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

