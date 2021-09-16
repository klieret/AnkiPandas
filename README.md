# Analyze and manipulate your Anki collection using pandas! 📇📈

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-9-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/klieret/AnkiPandas/master.svg)](https://results.pre-commit.ci/latest/github/klieret/AnkiPandas/master)
[![gh actions](https://github.com/klieret/AnkiPandas/workflows/testing/badge.svg)](https://github.com/klieret/AnkiPandas/actions)
[![Coveralls](https://coveralls.io/repos/github/klieret/AnkiPandas/badge.svg?branch=master)](https://coveralls.io/github/klieret/AnkiPandas?branch=master)
[![Documentation Status](https://readthedocs.org/projects/ankipandas/badge/?version=latest)](https://ankipandas.readthedocs.io/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/klieret/AnkiPandas.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/klieret/AnkiPandas/context:python)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![Pypi status](https://badge.fury.io/py/ankipandas.svg)](https://pypi.org/project/ankipandas/)
[![Gitter](https://img.shields.io/gitter/room/ankipandas/community.svg)](https://gitter.im/ankipandas/community)
[![License](https://img.shields.io/github/license/klieret/ankipandas.svg)](https://github.com/klieret/ankipandas/blob/master/LICENSE.txt)
[![PR welcome](https://img.shields.io/badge/PR-Welcome-%23FF8300.svg)](https://git-scm.com/book/en/v2/GitHub-Contributing-to-a-Project)

## 📝 Description

![image](https://raw.githubusercontent.com/klieret/AnkiPandas/master/misc/logo/logo_github.png)

[Anki](https://apps.ankiweb.net/) is one of the most popular flashcard
system for spaced repetition learning,
[pandas](https://pandas.pydata.org/) is the most popular python package
for data analysis and manipulation. So what could be better than to
bring both together?

With `AnkiPandas` you can use `pandas` to easily analyze or manipulate
your Anki flashcards.

**Features**:

-   **Select**: Easily select arbitrary subsets of your cards, notes or
    reviews using `pandas` ([one of many
    introductions](https://medium.com/dunder-data/6fcd0170be9c),
    [official
    documentation](https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html))
-   **Visualize**: Use pandas\' powerful [built in
    tools](https://pandas.pydata.org/pandas-docs/stable/user_guide/visualization.html)
    or switch to the even more versatile
    [seaborn](https://seaborn.pydata.org/) (statistical analysis) or
    [matplotlib](https://matplotlib.org/) libraries
-   **Manipulate & adding notes and cards**: Apply fast bulk operations to the table (e.g. add
    tags, change decks, set field contents, suspend cards, \...) or
    iterate over the table and perform these manipulations step by step. **This is still in alpha/beta! Proceed with care and please report bugs!** (but ankipandas will always create a backup of your database before changing something).
-   **Import and Export**: Pandas can export to (and import from) csv,
    MS Excel, HTML, JSON, \... ([io
    documentation](https://pandas.pydata.org/pandas-docs/stable/user_guide/io.html))

**Pros**:

-   **Easy installation**: Install via python package manager
    (independent of your Anki installation)
-   **Simple**: Just one line of code to get started
-   **Convenient**: Bring together information about
    [cards](https://apps.ankiweb.net/docs/manual.html#cards),
    [notes](https://apps.ankiweb.net/docs/manual.html#notes-&-fields),
    [models](https://apps.ankiweb.net/docs/manual.html#note-types),
    [decks](https://apps.ankiweb.net/docs/manual.html#decks) and more in
    just one table!
-   **Fully documented**: Documentation on [readthedocs](https://ankipandas.readthedocs.io/)
-   **Well tested**: More than 100 unit tests to keep everything in
    check

Alternatives: If your main goal is to add new cards, models and more,
you can also take a look at the
[genanki](https://github.com/kerrickstaley/genanki) project.

## 📦 Installation

`AnkiPandas` is available as [pypi
package](https://pypi.org/project/ankipandas/) and can be installed or
upgrade with the [python package
manager](https://pip.pypa.io/en/stable/):

```sh
pip3 install --user --upgrade ankipandas
```

For the latest development version you can also work from a cloned
version of this repository:

```sh
git clone https://github.com/klieret/ankipandas/
cd ankipandas
pip3 install --user --upgrade .
```

## 🔥 Let's get started!

Starting up is as easy as this:

```python
from ankipandas import Collection

col = Collection()
```

And `col.notes` will be dataframe containing all notes, with additional
methods that make many things easy. Similarly, you can access cards or
reviews using `col.cards` or `col.revs`.

If called without any argument `Collection()` tries to find your Anki
database by itself. However this might take some time. To make it
easier, simply supply (part of) the path to the database and (if you
have more than one user) your Anki user name, e.g.
`Collection(".local/share/Anki2/", user="User 1")` on many Linux
installations.

To get information about the interpretation of each column, use
`print(col.notes.help_cols())`.

Take a look at the [documentation](https://ankipandas.readthedocs.io/)
to find out more about more about the available methods!

Some basic examples:

## 📈 Analysis

**More examples**: [Analysis
documentation](https://ankipandas.readthedocs.io/en/latest/examples.html)

Show a histogram of the number of reviews (repetitions) of each card for
all decks:

```python
col.cards.hist(column="creps", by="cdeck")
```

Show the number of leeches per deck as pie chart:

```python
cards = col.cards.merge_notes()
selection = cards[cards.has_tag("leech")]
selection["cdeck"].value_counts().plot.pie()
```

Find all notes of model `MnemoticModel` with empty `Mnemotic` field:

```python
notes = col.notes.fields_as_columns()
notes.query("model=='MnemoticModel' and 'Mnemotic'==''")
```

## 🛠️ Manipulations

**Please be careful and test this well!** Ankipandas will create a backup of your database before writing, so you can always restore the previous state. Please make sure that everything is working before continuing to use Anki normally!

Add the `difficult-japanese` and `marked` tag to all notes that contain
the tags `Japanese` and `leech`:

```python
notes = col.notes
selection = notes[notes.has_tags(["Japanese", "leech"])]
selection = selection.add_tag(["difficult-japanese", "marked"])
col.notes.update(selection)
col.write(modify=True)  # Overwrites your database after creating a backup!
```

Set the `language` field to `English` for all notes of model
`LanguageModel` that are tagged with `English`:

```python
notes = col.notes
selection = notes[notes.has_tag(["English"])].query("model=='LanguageModel'").copy()
selection.fields_as_columns(inplace=True)
selection["language"] = "English"
col.notes.update(selection.fields_as_list())
col.write(modify=True)
```

Move all cards tagged `leech` to the deck `Leeches Only`:

```python
cards = col.cards
selection = cards[cards.has_tag("leech")]
selection["cdeck"] = "Leeches Only"
col.cards.update(selection)
col.write(modify=True)
```

## 🐞 Troubleshooting

See the [troubleshooting section in the
documentation](https://ankipandas.readthedocs.io/en/latest/troubleshooting.html).

## 💖 Contributing

Your help is greatly appreciated! Suggestions, bug reports and feature
requests are best opened as [github
issues](https://github.com/klieret/ankipandas/issues). You could also
first discuss in the [gitter
community](https://gitter.im/ankipandas/community). If you want to code
something yourself, you are very welcome to submit a [pull
request](https://github.com/klieret/AnkiPandas/pulls)!

Bug reports and pull requests are credited with the help of the [allcontributors bot](https://allcontributors.org/).

## 📃 License & Disclaimer

This software is licenced under the [MIT
license](https://github.com/klieret/ankipandas/blob/master/LICENSE.txt)
and (despite best testing efforts) comes **without any warranty**. The
logo is inspired by the [Anki
logo](https://github.com/dae/anki/blob/master/web/imgs/anki-logo-thin.png)
([license](https://github.com/dae/anki/blob/master/LICENSE.logo)) and
the [logo of the pandas
package](https://github.com/pandas-dev/pandas/blob/master/doc/logo/pandas_logo.svg)
([license2](https://github.com/pandas-dev/pandas/blob/master/LICENSE)).
This library and its author(s) are not affiliated/associated with the
main Anki or pandas project in any way.

## ✨ Contributors

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/Blocked"><img src="https://avatars.githubusercontent.com/u/4366503?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Blocked</b></sub></a><br /><a href="https://github.com/klieret/AnkiPandas/issues?q=author%3ABlocked" title="Bug reports">🐛</a></td>
    <td align="center"><a href="https://github.com/CalculusAce"><img src="https://avatars3.githubusercontent.com/u/42630988?v=4?s=100" width="100px;" alt=""/><br /><sub><b>CalculusAce</b></sub></a><br /><a href="https://github.com/klieret/AnkiPandas/issues?q=author%3ACalculusAce" title="Bug reports">🐛</a></td>
    <td align="center"><a href="https://github.com/khughitt"><img src="https://avatars.githubusercontent.com/u/125001?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Keith Hughitt</b></sub></a><br /><a href="https://github.com/klieret/AnkiPandas/issues?q=author%3Akhughitt" title="Bug reports">🐛</a></td>
    <td align="center"><a href="https://github.com/eumiro"><img src="https://avatars0.githubusercontent.com/u/6774676?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Miroslav Šedivý</b></sub></a><br /><a href="https://github.com/klieret/AnkiPandas/commits?author=eumiro" title="Tests">⚠️</a> <a href="https://github.com/klieret/AnkiPandas/commits?author=eumiro" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/bollwyvl"><img src="https://avatars.githubusercontent.com/u/45380?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Nicholas Bollweg</b></sub></a><br /><a href="https://github.com/klieret/AnkiPandas/commits?author=bollwyvl" title="Code">💻</a></td>
    <td align="center"><a href="http://thomasbrownback.com/"><img src="https://avatars2.githubusercontent.com/u/26754?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Thomas Brownback</b></sub></a><br /><a href="https://github.com/klieret/AnkiPandas/issues?q=author%3Abrownbat" title="Bug reports">🐛</a></td>
    <td align="center"><a href="http://esrh.sdf.org"><img src="https://avatars.githubusercontent.com/u/16175276?v=4?s=100" width="100px;" alt=""/><br /><sub><b>eshrh</b></sub></a><br /><a href="https://github.com/klieret/AnkiPandas/commits?author=eshrh" title="Documentation">📖</a></td>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/exc4l"><img src="https://avatars3.githubusercontent.com/u/74188442?v=4?s=100" width="100px;" alt=""/><br /><sub><b>exc4l</b></sub></a><br /><a href="https://github.com/klieret/AnkiPandas/issues?q=author%3Aexc4l" title="Bug reports">🐛</a> <a href="https://github.com/klieret/AnkiPandas/commits?author=exc4l" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/p4nix"><img src="https://avatars1.githubusercontent.com/u/7038116?v=4?s=100" width="100px;" alt=""/><br /><sub><b>p4nix</b></sub></a><br /><a href="https://github.com/klieret/AnkiPandas/issues?q=author%3Ap4nix" title="Bug reports">🐛</a></td>
  </tr>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!
