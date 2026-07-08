# Posterfolio Milestone 16D - IMDb aria-label capture

Files changed:
- src/poster_montage_designer/services/imdb_capture.py

Changes:
- Resets IMDb capture to use visible `/title/tt...` links.
- Uses `aria-label` as the primary title source because IMDb filmography links often have empty visible text.
- Deduplicates repeated IMDb title links.

Commit message:
Use IMDb aria labels for embedded credit capture
