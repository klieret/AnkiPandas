Troubleshooting
---------------

Getting help
^^^^^^^^^^^^

Submit an `issue on github`_ or write in the `gitter community`_. Thank you for
improving this toolkit with me!

.. _issue on github: https://github.com/klieret/ankipandas/issues
.. _gitter community: https://gitter.im/AnkiPandas/community

Common problems
^^^^^^^^^^^^^^^

* **Locked database**: While Anki is running, your database will be locked and
  you might not be able to access it. Simply close Anki and try again. Similarly
  Anki might refuse to open the database if ``ankipandas`` has currently opened
  it (be it in a Jupyter notebook or in a currently running project).

.. note::

    Any unlisted problem that you ran into (and solved)? Help others by bringing
    it to my attention_. Please check if there is already an issue created for
    it by going through this list_.

.. _attention: https://github.com/klieret/ankipandas/issues
.. _list: https://github.com/klieret/AnkiPandas/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc+label%3Abug


Debugging
^^^^^^^^^

For better debugging, you can increase the log level of ``ankipandas``:

.. code-block:: python

    ankipandas.set_log_level("debug")
