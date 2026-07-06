from __future__ import annotations

import urllib.error
import urllib.request
from pathlib import Path

from poster_montage_designer.paths import (
    POSTER_ORIGINAL_CACHE_DIR,
    POSTER_W500_CACHE_DIR,
    ensure_app_dirs,
)
from poster_montage_designer.services.tmdb import TmdbError, lookup_imdb_id


TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

VALID_POSTER_SIZES = {
    "w500": POSTER_W500_CACHE_DIR,
    "original": POSTER_ORIGINAL_CACHE_DIR,
}


class PosterError(RuntimeError):
    pass


def get_poster(imdb_title_id: str, *, size: str = "w500") -> Path | None:
    ensure_app_dirs()

    if size not in VALID_POSTER_SIZES:
        raise PosterError(f"Unsupported poster size: {size}")

    cache_dir = VALID_POSTER_SIZES[size]
    poster_path = cache_dir / f"{imdb_title_id}.jpg"

    if poster_path.exists():
        return poster_path

    metadata = lookup_imdb_id(imdb_title_id)

    if metadata is None:
        return None

    if not metadata.poster_path:
        return None

    url = f"{TMDB_IMAGE_BASE_URL}/{size}{metadata.poster_path}"

    try:
        _download_file(url, poster_path)
    except TmdbError:
        raise
    except Exception as error:
        raise PosterError(f"Could not download poster for {imdb_title_id}: {error}") from error

    return poster_path


def _download_file(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "PosterMontageDesigner/0.1",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
    except urllib.error.HTTPError as error:
        raise PosterError(f"Poster HTTP error {error.code}: {url}") from error
    except urllib.error.URLError as error:
        raise PosterError(f"Could not connect to poster server: {error}") from error

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)