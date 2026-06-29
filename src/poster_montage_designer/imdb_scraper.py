from __future__ import annotations

import re
from collections import OrderedDict
from urllib.parse import urljoin

from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError

from .models import ImdbTitle

TITLE_ID_RE = re.compile(r"/title/(tt\d+)/")
YEAR_RE = re.compile(r"(?:19|20)\d{2}")


async def scrape_imdb_person_titles(person_url: str, *, headed: bool = False, slow_mo: int = 0) -> list[ImdbTitle]:
    """Open an IMDb person page in Chromium and extract visible title links.

    This intentionally behaves like a browser user rather than using Cinemagoer.
    It tries to expand/click "See all" style controls, then extracts all /title/tt... links.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not headed, slow_mo=slow_mo)
        page = await browser.new_page(viewport={"width": 1600, "height": 1200})
        await page.goto(person_url, wait_until="domcontentloaded", timeout=60_000)
        await _accept_or_dismiss_overlays(page)
        await _expand_credit_sections(page)
        await _scroll_to_bottom(page)
        await _expand_credit_sections(page)
        titles = await _extract_title_links(page, person_url)
        await browser.close()
        return titles


async def _accept_or_dismiss_overlays(page: Page) -> None:
    labels = [
        "Accept",
        "Accept all",
        "I agree",
        "Agree",
        "Continue",
        "Close",
    ]
    for label in labels:
        try:
            button = page.get_by_role("button", name=re.compile(label, re.I)).first
            if await button.count():
                await button.click(timeout=1500)
                await page.wait_for_timeout(500)
        except Exception:
            pass


async def _expand_credit_sections(page: Page) -> None:
    patterns = [
        r"see all",
        r"show all",
        r"expand",
        r"more",
    ]
    for _ in range(4):
        clicked = 0
        for pattern in patterns:
            loc = page.get_by_role("button", name=re.compile(pattern, re.I))
            count = min(await loc.count(), 20)
            for i in range(count):
                try:
                    btn = loc.nth(i)
                    if await btn.is_visible():
                        await btn.click(timeout=1500)
                        clicked += 1
                        await page.wait_for_timeout(300)
                except Exception:
                    pass

            # Some IMDb expanders are links, not buttons.
            link = page.get_by_role("link", name=re.compile(pattern, re.I))
            count = min(await link.count(), 20)
            for i in range(count):
                try:
                    lnk = link.nth(i)
                    if await lnk.is_visible():
                        # If this navigates to a full credits page, allow it.
                        await lnk.click(timeout=1500)
                        clicked += 1
                        await page.wait_for_load_state("domcontentloaded", timeout=5000)
                        await page.wait_for_timeout(300)
                except PlaywrightTimeoutError:
                    pass
                except Exception:
                    pass
        if clicked == 0:
            break


async def _scroll_to_bottom(page: Page) -> None:
    last_height = 0
    for _ in range(12):
        height = await page.evaluate("document.body.scrollHeight")
        if height == last_height:
            break
        last_height = height
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(800)


async def _extract_title_links(page: Page, base_url: str) -> list[ImdbTitle]:
    raw_links = await page.evaluate(
        """
        () => Array.from(document.querySelectorAll('a[href*="/title/tt"]')).map(a => {
            const href = a.getAttribute('href') || '';
            const text = (a.innerText || a.textContent || '').trim();
            let context = '';
            let node = a;
            for (let i = 0; i < 5 && node; i++) {
                context += ' ' + (node.innerText || node.textContent || '');
                node = node.parentElement;
            }
            return {href, text, context};
        })
        """
    )

    found: OrderedDict[str, ImdbTitle] = OrderedDict()
    for item in raw_links:
        href = item.get("href") or ""
        match = TITLE_ID_RE.search(href)
        if not match:
            continue
        imdb_id = match.group(1)
        text = _clean_title(item.get("text") or "")
        if not text or _looks_like_noise(text):
            continue
        context = item.get("context") or ""
        year_match = YEAR_RE.search(context)
        year = year_match.group(0) if year_match else None
        found.setdefault(
            imdb_id,
            ImdbTitle(
                title=text,
                imdb_title_id=imdb_id,
                year=year,
                url=urljoin(base_url, f"/title/{imdb_id}/"),
            ),
        )

    return list(found.values())


def _clean_title(text: str) -> str:
    text = " ".join(text.split())
    text = re.sub(r"^\d+\.\s*", "", text)
    return text.strip()


def _looks_like_noise(text: str) -> bool:
    lower = text.lower()
    if len(text) < 2:
        return True
    noise = {
        "see all",
        "show all",
        "more",
        "trailer",
        "official trailer",
        "video",
        "photos",
    }
    return lower in noise
