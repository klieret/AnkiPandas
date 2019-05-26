AnkiDataFrame
=============

The class :class:`~ankipandas.ankidf.AnkiDataFrame` is the central data
structure in which we provide the notes, cards and review tables.
Access it via an instance of :class:`~ankipandas.collection.Collection`.

Example:

.. code-block:: python

    from ankipandas import Collection
    col = Collection()

    col.notes  # Notes as AnkiDataFrame
    col.cards  # Cards as AnkiDataFrame
    col.revs   # Reviews as AnkiDataFrame

.. autoclass:: ankipandas.ankidf.AnkiDataFrame
    :members:
    :undoc-members:
    :exclude-members: equals, update, append
