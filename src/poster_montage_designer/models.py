from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Title:
    title: str
    year: int | None = None
    imdb_title_id: str | None = None
    url: str | None = None
    poster_path: Path | None = None


# Backwards compatibility for old scraper/importer files.
ImdbTitle = Title


@dataclass
class Project:
    name: str = "Untitled Montage"
    path: Path | None = None
    source: str = "None"
    titles: list[Title] = field(default_factory=list)
    dirty: bool = False

    @property
    def title_count(self) -> int:
        return len(self.titles)