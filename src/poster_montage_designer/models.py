from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Film:
    title: str
    year: int | None = None
    imdb_id: str | None = None
    poster_path: Path | None = None


@dataclass
class Project:
    name: str = "Untitled Montage"
    path: Path | None = None
    source: str = "None"
    films: list[Film] = field(default_factory=list)
    dirty: bool = False

    @property
    def film_count(self) -> int:
        return len(self.films)