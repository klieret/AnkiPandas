Questions & Answers
===================

> What do the different columns mean?

Please use the `help`, `help_cols`, or `help_col` methods of the `AnkiDataFrame`
object to display information about the columns.

> How to get the creation time of a card/note?

The IDs of the cards/notes correspond to the creation time.
See [issue #112](https://github.com/klieret/AnkiPandas/issues/112) for a small
code snippet to convert it to a ``datetime`` object.

> Can I access deck settings (e.g., the card intake per day) from `ankipandas`?

This is currently not supported by `ankipandas`. However, you can find related
discussion in [issue #113](https://github.com/klieret/AnkiPandas/issues/113).
