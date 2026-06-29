from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .imdb_scraper import scrape_imdb_person_titles

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(prog="poster_montage_designer")
    sub = parser.add_subparsers(dest="command", required=True)

    scrape = sub.add_parser("scrape-imdb", help="Extract title links from an IMDb person page using a rendered browser")
    scrape.add_argument("url", help="IMDb person URL, e.g. https://www.imdb.com/name/nm0846880/")
    scrape.add_argument("--out", default="projects/titles.json", help="Output JSON path")
    scrape.add_argument("--headed", action="store_true", help="Show the browser while scraping")
    scrape.add_argument("--slow", type=int, default=0, help="Slow Playwright actions by N milliseconds")

    args = parser.parse_args()

    if args.command == "scrape-imdb":
        titles = asyncio.run(scrape_imdb_person_titles(args.url, headed=args.headed, slow_mo=args.slow))
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps([t.to_dict() for t in titles], indent=2, ensure_ascii=False), encoding="utf-8")

        table = Table(title=f"IMDb titles found: {len(titles)}")
        table.add_column("#", justify="right")
        table.add_column("Year")
        table.add_column("Title")
        table.add_column("IMDb ID")

        for i, title in enumerate(titles, start=1):
            table.add_row(str(i), title.year or "", title.title, title.imdb_title_id or "")

        console.print(table)
        console.print(f"\nSaved: [bold]{out_path}[/bold]")


if __name__ == "__main__":
    main()
