# Posterfolio v1.0 RC2

## Files changed
- `src/poster_montage_designer/windows/main_window.py`
- `src/poster_montage_designer/widgets/workspace.py`
- `src/poster_montage_designer/widgets/title_list.py` *(new)*
- `src/poster_montage_designer/services/posters.py`
- `src/poster_montage_designer/app.py`

## Changes
- Posters now lift from the canvas and follow the pointer during a real Qt drag operation.
- The source cell is left empty until the drag ends.
- Canvas-to-canvas drops swap posters; invalid drops restore the source.
- Bench titles can be dragged onto a canvas poster to replace it.
- Canvas posters can be dragged onto the Bench list.
- Added live Imported / Visible / Benched / Missing project summary.
- Poster candidates prefer English-tagged artwork; if none exists, Posterfolio falls back to the available catalogue.
- Candidates are ordered by vote count, then vote average.
- Existing catalogue/image caches are safely refreshed when candidate ordering changes.
- Poster controls display `Poster 4 of 37`, or `Poster` for a single candidate.
- Nearby poster variants are quietly prefetched to make arrow browsing faster.

## Test checklist
1. Open an existing project and confirm its canvas rebuilds.
2. Drag a canvas poster over another and confirm they swap.
3. Start a canvas drag and release outside a valid target; confirm it restores.
4. Drag a Bench title over a canvas poster; confirm the displaced title moves to Bench.
5. Drag a canvas poster onto Bench.
6. Confirm Undo works after each operation.
7. Browse poster variants and confirm the label and ordering.
8. Confirm the project summary updates after bench/promote/delete operations.

## Commit message
`Add release candidate drag and poster workflow polish`
