# Changelog

## 0.1.0
2026-08-28

First release since 0.0.4 (2022-01-13); it carries three unpublished 2022 commits as well as
this month's pandas 2 fix.

### Added
- `get_project_metadata(project_ids_dict)`: takes the dict returned by
  `get_project_ids_from_bounds` and returns a dataframe of metadata for every NADAG project in
  it, with the borehole count, the fact-sheet, download and `stack.zip` URLs, and the numeric
  NADAG project id resolved into their own columns. The helpers `get_stack_zip_url` and
  `get_nadag_id_from_url` come with it. Documented in the README.

### Changed
- NGU moved its WFS server: `get_project_ids_from_bounds` now queries
  `https://geo.ngu.no/geoserver/nadag/wfs` over **WFS 2.0.0** rather than the old `http://`
  endpoint over 1.1.0, and no longer passes `srsname` (2.0.0 rejects the URN form 1.1.0
  wanted). Bounding-box lookups do not work against the live server without this.
- The module constant `WMS_SERVER` is renamed `WFS_SERVER` to match. Breaking for anything
  importing it by name; nothing in the EMerald stack does.

### Fixed
- pandas 2 compatibility: `map_nadag_attributes` replaces `pandas.DataFrame.append` (removed in
  pandas 2.0) with `pandas.concat` of a one-row frame. `ignore_index=True` was already in use,
  so the resulting 0..n-1 index is unchanged.
