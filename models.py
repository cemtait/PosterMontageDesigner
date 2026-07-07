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
    selected_poster_index: int = 0
    benched: bool = False
    bench_reason: str = ""
    missing_poster: bool = False
    revenue: int | None = None


# Backwards compatibility for old IMDb importer/scraper modules.
ImdbTitle = Title


@dataclass
class Page:
    name: str
    canvas_color: str = "#000000"
    airiness: int = 50
    page_width_mm: float = 27.0 * 25.4
    page_height_mm: float = 40.0 * 25.4
    canvas_preset: str = "One Sheet 27 × 40 in"
    layout_order: list[str] = field(default_factory=list)

    def clone(self, name: str) -> "Page":
        return Page(
            name=name,
            canvas_color=self.canvas_color,
            airiness=self.airiness,
            page_width_mm=self.page_width_mm,
            page_height_mm=self.page_height_mm,
            canvas_preset=self.canvas_preset,
            layout_order=list(self.layout_order),
        )


@dataclass
class Project:
    name: str = "Untitled Posterfolio"
    path: Path | None = None
    source: str = "None"
    titles: list[Title] = field(default_factory=list)
    dirty: bool = False
    pages: list[Page] = field(default_factory=lambda: [Page(name="Main")])
    current_page_index: int = 0

    @property
    def title_count(self) -> int:
        return len(self.titles)

    @property
    def active_titles(self) -> list[Title]:
        return [title for title in self.titles if not title.benched]

    @property
    def benched_titles(self) -> list[Title]:
        return [title for title in self.titles if title.benched]

    @property
    def benched_count(self) -> int:
        return len(self.benched_titles)

    @property
    def rejected_count(self) -> int:
        return self.benched_count

    @property
    def current_page(self) -> Page:
        if not self.pages:
            self.pages.append(Page(name="Main"))
        self.current_page_index = max(0, min(self.current_page_index, len(self.pages) - 1))
        return self.pages[self.current_page_index]

    def active_imdb_ids(self) -> list[str]:
        return [title.imdb_title_id for title in self.active_titles if title.imdb_title_id]

    def title_by_imdb_id(self, imdb_title_id: str) -> Title | None:
        for title in self.titles:
            if title.imdb_title_id == imdb_title_id:
                return title
        return None

    # Compatibility layer: old code can still read/write these on Project,
    # but the values now belong to the current Page.
    @property
    def layout_order(self) -> list[str]:
        return self.current_page.layout_order

    @layout_order.setter
    def layout_order(self, value: list[str]) -> None:
        self.current_page.layout_order = value

    @property
    def canvas_color(self) -> str:
        return self.current_page.canvas_color

    @canvas_color.setter
    def canvas_color(self, value: str) -> None:
        self.current_page.canvas_color = value

    @property
    def airiness(self) -> int:
        return self.current_page.airiness

    @airiness.setter
    def airiness(self, value: int) -> None:
        self.current_page.airiness = value

    @property
    def page_width_mm(self) -> float:
        return self.current_page.page_width_mm

    @page_width_mm.setter
    def page_width_mm(self, value: float) -> None:
        self.current_page.page_width_mm = value

    @property
    def page_height_mm(self) -> float:
        return self.current_page.page_height_mm

    @page_height_mm.setter
    def page_height_mm(self, value: float) -> None:
        self.current_page.page_height_mm = value

    @property
    def canvas_preset(self) -> str:
        return self.current_page.canvas_preset

    @canvas_preset.setter
    def canvas_preset(self, value: str) -> None:
        self.current_page.canvas_preset = value
