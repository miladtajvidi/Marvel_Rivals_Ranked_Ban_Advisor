from __future__ import annotations

import re
from dataclasses import dataclass

from src.models import HeroStat
from src.name_matching import is_exact_profile_match, normalize_player_name
from src.rivalsmeta import SearchResult


@dataclass(frozen=True)
class VisiblePlayerResult:
    name: str
    href: str


class BrowserRivalsMetaClient:
    def __init__(
        self,
        *,
        base_url: str = "https://rivalsmeta.com",
        headless: bool = True,
        timeout_ms: int = 20_000,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._playwright = None
        self._browser = None
        self._page = None

    def __enter__(self) -> "BrowserRivalsMetaClient":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def start(self) -> None:
        if self._page is not None:
            return

        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Playwright is not installed. Install browser extras with "
                "`pip install -e .[browser]`."
            ) from exc

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._page = self._browser.new_page()
        self._page.goto(self.base_url, wait_until="domcontentloaded", timeout=self.timeout_ms)

    def close(self) -> None:
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()
        self._playwright = None
        self._browser = None
        self._page = None

    def search_player(self, player_name: str) -> list[SearchResult]:
        page = self._require_page()
        normalized = normalize_player_name(player_name)
        if not normalized:
            return []

        page.goto(self.base_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        search_area = page.locator("section").filter(has_text="Marvel Rivals Tracker")
        search_input = search_area.get_by_placeholder("Search by player name or paste a UID")
        search_input.fill(normalized, timeout=self.timeout_ms)
        page.wait_for_timeout(500)

        players = search_area.locator('a[href^="/player/"]')
        try:
            players.first.wait_for(state="visible", timeout=self.timeout_ms)
        except Exception:
            return []

        visible_results = []
        for index in range(players.count()):
            player_link = players.nth(index)
            name = extract_player_name_from_link_text(player_link.inner_text(timeout=2_000))
            href = player_link.get_attribute("href", timeout=2_000) or ""
            if name and href:
                visible_results.append(VisiblePlayerResult(name=name, href=href))

        return [
            SearchResult(
                display_name=result.name,
                profile_url=_absolute_url(self.base_url, result.href),
            )
            for result in select_exact_visible_results(normalized, visible_results)
        ] or self._find_and_verify_current_profile(search_area, normalized)

    def fetch_competitive_heroes(self, profile_url: str) -> tuple[HeroStat, ...]:
        page = self._require_page()
        page.goto(profile_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
        page.wait_for_timeout(1_500)
        text = normalize_player_name(page.locator("body").inner_text(timeout=self.timeout_ms))
        return parse_visible_competitive_heroes(text)

    def _find_and_verify_current_profile(self, search_area, player_name: str) -> list[SearchResult]:
        page = self._require_page()
        find_button = search_area.get_by_role("button", name="Find", exact=True)
        if find_button.count() != 1 or not find_button.is_enabled():
            return []

        find_button.click(timeout=self.timeout_ms)
        try:
            page.wait_for_url("**/player/**", timeout=self.timeout_ms)
            page.wait_for_load_state("domcontentloaded", timeout=self.timeout_ms)
            page.get_by_role("heading", name=player_name, exact=True).wait_for(
                state="visible",
                timeout=self.timeout_ms,
            )
        except Exception:
            return []

        heading = normalize_player_name(page.locator("h1").inner_text(timeout=self.timeout_ms))
        if not is_exact_profile_match(player_name, heading):
            return []

        return [SearchResult(display_name=heading, profile_url=page.url)]

    def _require_page(self):
        self.start()
        if self._page is None:
            raise RuntimeError("Browser page was not initialized.")
        return self._page


def select_exact_visible_results(
    requested_name: str,
    results: list[VisiblePlayerResult],
) -> list[VisiblePlayerResult]:
    exact = [result for result in results if is_exact_profile_match(requested_name, result.name)]
    return exact if len(exact) == 1 else []


def extract_player_name_from_link_text(text: str) -> str:
    lines = [
        normalize_player_name(line)
        for line in text.splitlines()
        if normalize_player_name(line)
    ]
    if not lines:
        return ""

    for line in reversed(lines):
        if line.casefold() not in {"player image"}:
            return line
    return ""


def parse_visible_competitive_heroes(text: str) -> tuple[HeroStat, ...]:
    competitive_text = _competitive_slice(text)
    hero_stats: list[HeroStat] = []

    # Handles compact visible rows like:
    # Hela 24 Games 58% Win Rate
    pattern = re.compile(
        r"(?P<hero>[A-Z][A-Za-z .'-]{2,40})\s+"
        r"(?P<games>\d{1,4})\s+(?:Games?|Matches?)\s+"
        r"(?P<win_rate>\d{1,3}(?:\.\d+)?)%",
        re.IGNORECASE,
    )
    reverse_pattern = re.compile(
        r"(?P<hero>[A-Z][A-Za-z .'-]{2,40})\s+"
        r"(?:\d+(?:\.\d+)?\s*KDA\s+)?"
        r"(?:\d+(?:\.\d+)?/\d+(?:\.\d+)?/\d+(?:\.\d+)?\s+)?"
        r"(?P<win_rate>\d{1,3}(?:\.\d+)?)%\s+"
        r"(?P<games>\d{1,4})\s+(?:games?|matches?)",
        re.IGNORECASE,
    )
    compact_pattern = re.compile(
        r"(?:Top Heroes)?(?:Competitive)?(?:Quick Play)?"
        r"(?P<hero>[A-Z][A-Za-z .'-]{2,40}?)"
        r"\d+(?:\.\d+)?\s*KDA"
        r"\d+(?:\.\d+)?/\d+(?:\.\d+)?/(?P<assist_and_win_rate>\d+(?:\.\d+)?)%"
        r"(?P<games>\d{1,4})\s*games?",
        re.IGNORECASE,
    )
    for match in [
        *pattern.finditer(competitive_text),
        *reverse_pattern.finditer(competitive_text),
    ]:
        hero_name = normalize_player_name(match.group("hero"))
        if _looks_like_stat_label(hero_name):
            continue
        hero_stats.append(
            HeroStat(
                hero_name=hero_name,
                games_played=int(match.group("games")),
                win_rate=float(match.group("win_rate")) / 100,
            )
        )

    for match in compact_pattern.finditer(competitive_text):
        hero_name = normalize_player_name(match.group("hero"))
        if _looks_like_stat_label(hero_name):
            continue

        win_rate_text = _extract_glued_win_rate(match.group("assist_and_win_rate"))
        hero_stats.append(
            HeroStat(
                hero_name=hero_name,
                games_played=int(match.group("games")),
                win_rate=float(win_rate_text) / 100,
            )
        )

    return tuple(_dedupe_hero_stats(hero_stats))


def _competitive_slice(text: str) -> str:
    lowered = text.casefold()
    start = lowered.find("top heroes")
    if start == -1:
        start = lowered.find("competitive")
    if start == -1:
        return text

    end_candidates = [
        lowered.find(marker, start + len("competitive"))
        for marker in ("teammates", "match history", "overview")
    ]
    quick_play_index = lowered.find("quick play", start + len("competitive"))
    if quick_play_index != -1 and "games" in lowered[start:quick_play_index]:
        end_candidates.append(quick_play_index)
    end_candidates = [index for index in end_candidates if index != -1]
    end = min(end_candidates) if end_candidates else len(text)
    return text[start:end]


def _looks_like_stat_label(hero_name: str) -> bool:
    return hero_name.casefold() in {
        "competitive",
        "hero",
        "heroes",
        "win rate",
        "games",
        "matches",
    }


def _extract_glued_win_rate(assist_and_win_rate: str) -> str:
    normalized = assist_and_win_rate.strip()
    if "." in normalized:
        return normalized
    stripped = normalized.lstrip("0")
    if not stripped:
        return "0"
    return stripped[-3:] if len(stripped) > 3 else stripped


def _dedupe_hero_stats(stats: list[HeroStat]) -> list[HeroStat]:
    deduped: dict[str, HeroStat] = {}
    for stat in stats:
        deduped.setdefault(stat.hero_name.casefold(), stat)
    return list(deduped.values())


def _absolute_url(base_url: str, href: str) -> str:
    if href.startswith("http"):
        return href
    return f"{base_url.rstrip('/')}/{href.lstrip('/')}"
