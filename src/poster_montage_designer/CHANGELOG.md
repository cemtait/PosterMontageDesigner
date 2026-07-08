# Posterfolio Milestone 15 Fix - IMDb Capture

## Changed files

- `src/poster_montage_designer/services/imdb_capture.py`

## What changed

- Replaces the first DOM-only IMDb extractor with a more robust extractor.
- Reads embedded IMDb JSON data when available.
- Keeps the visible-link DOM fallback for pages where links are present.
- Leaves the browser dialog and the rest of the app unchanged.

## Commit message

`Improve embedded IMDb credit capture`
