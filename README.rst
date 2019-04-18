AnkiPandas: Open your Anki database as a pandas DataFrame in just one line!
===========================================================================

.. start-body

Description
-----------

With this small python package, you can easily load all of your Anki flashcards
as a all-in-one pandas DataFrame!

Pros:

* Use all of your mighty pandas tools to data science the heck out of
  your Anki collection
* Just one line of code to get your data frame containing all the information
  you need
* Bring together information about cards, notes and models in just one object!
  There's no need to go from cards to corresponding notes to corresponding
  note model just to find out the field names and contents.
* Easy installation (does not depend on any anki installation)

Cons:

* This package does not aim to write back to your database, there's other
  (more complex) packages out there that help with that!

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
    cd clusterking
    pip3 install --user .

Usage
-----

It's as easy as this:

.. code:: python

    import ankipandas

    ankipandas.get_cards_df("/path/to/your/anki/adatabase/collection.anki2")

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
