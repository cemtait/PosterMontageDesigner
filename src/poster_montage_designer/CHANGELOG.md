# Posterfolio v1.0 RC1 — RC1–RC3 Combined

## Files changed

- `src/poster_montage_designer/app.py`
- `src/poster_montage_designer/models.py`
- `src/poster_montage_designer/windows/main_window.py`
- `src/poster_montage_designer/dialogs/export_dialog.py`
- `src/poster_montage_designer/dialogs/imdb_import_dialog.py`

## Files added

- `src/poster_montage_designer/dialogs/settings_dialog.py`
- `src/poster_montage_designer/version.py`

## Included

- Project terminology throughout File menus and dialogs.
- Bookmarklet/IMDb-file import removed from the visible UI.
- Main Project-panel import button now opens the embedded IMDb importer.
- Clean modular Settings dialog.
- Remembers last project folder, last export folder, window geometry, and splitter positions.
- Export format dropdown styling now matches the rest of the application.
- IMDb developer diagnostics hidden by default; diagnostic code retained.
- IMDb import debug printing removed.
- Help > About Posterfolio dialog and release-candidate version number.
- Right-click Title List menu: Select Poster, Open on IMDb, Bench, Delete from Project.
- Right-click Bench menu: Open on IMDb, Promote, Delete from Project.
- Permanent project deletion supports multi-selection, confirmation, and Ctrl+Z undo.
- Mojibake cleanup for multiplication signs and window-title separators.

## Deliberately not included yet

- Poster-following-mouse drag visuals.
- Bench-to-canvas and canvas-to-bench drag/drop.
- Project summary/dashboard.
- Ranking or hero-title controls.

## Suggested commit message

`Combine release candidate polish, settings, and title management`
