# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.3.11 -- 2022-12-29

### Removed

- Python 3.6 has reached its end of life and is no longer supported. This is to
  ensure that we can keep the code base modern and developers happy.

### Fixed

- When updating cards or notes, certain SQL search indices that are usually
  automatically created by Anki could be left missing. While these do not
  change any of the information in the database and can be created trivially,
  this caused Anki to refuse to load the database.

### Documentation and developer happiness

- Various improvements to the documentation
- Work on modernizing the code base

## 0.3.10 -- 2021-05-07

### Fixed

- The SQLite connection to the database is now always closed right away by the Collection.
  This solves issues where the connection was kept open even though all collection and
  AnkiDataFrame objects were deleted (there is additional garbage collection trouble).
  Read more in [issue 75](https://github.com/klieret/AnkiPandas/issues/75)

## 0.3.9 -- 2020-12-17

### Deprecated

- Future releases will not support python 3.5 anymore. Added warning for users still on
  python 3.5.

## 0.3.8 -- 2020-12-05

### Fixed

- Setup problems with editable install as described [here](https://github.com/pypa/pip/issues/7953)
- Compatibility issues with building ankipandas on windows machines (windows is not
  using utf8 by default which often results in errors, see
  [here](https://discuss.python.org/t/pep-597-enable-utf-8-mode-by-default-on-windows/3122))
- Issues with max search depth for database search
- AttributeError when calling `merge_notes` with `inplace=True`. [Issue #51](https://github.com/klieret/AnkiPandas/issues/51)
- Default search paths might not have been working because the user name was not inserted properly
- Properly tell anki that things were changed and that it should sync its tables

### Changed

- Improved database search on windows machines
- If no changes are detected in the different tables, the database will not be overwritten

## 0.3.7 -- 2020-11-28

### Fixed

- `merge_cards` and `merge_notes` didn't update metadata of return value, resulting in errors like
  `Unknown value of _df_format`. Issue #42
- `force` values weren't passed on, resulting in AnkiPandas refusing to do anything
  when writing out
- On Windows the int size is 32 bit even on 64 bit computers, resulting in issues with
  large values of ids. Issue #41


## 0.3.6 - 2020-08-26

### Fixed

- Keep support for python 3.5

## 0.3.5 - 2020-08-26

### Fixed

- Support for new anki versions ([#38](https://github.com/klieret/AnkiPandas/issues/38))

## 0.3.4 - 2020-07-09

### Fixed

- JSONDecodeError upon loading database. Also added additional debugging output in case something like this happens again.

## 0.3.3 - 2020-04-21

### Fixed

- Compatibility with new pandas versions

## 0.3.0 - 2019-06-02

### Added

- Add new notes and cards

### Changed

- Cards/notes/reviews tables are now initialized from a central ``Collection`` object

### Fixed

- ``was_modified``, ``was_added`` break when user added additional columns to dataframe
- Correctly set ``mod`` (modification timestamp) and ``usn`` (update sequence number) of whole database after updates

## 0.2.1 - 2019-05-17

### Fixed

- Merging of tables failed with some pandas versions

## 0.2.0 - 2019-05-07

### Added

- Modify tables and write them back into the database.
