# Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
