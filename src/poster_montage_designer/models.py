from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(slots=True)
class ImdbTitle:
    title: str
    imdb_title_id: str | None = None
    year: str | None = None
    url: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
