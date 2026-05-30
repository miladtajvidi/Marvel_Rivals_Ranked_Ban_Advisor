from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from src.models import HeroStat, PlayerProfile
from src.name_matching import is_exact_profile_match, is_hidden_streamer_name, normalize_player_name


@dataclass(frozen=True)
class SearchResult:
    display_name: str
    profile_url: str


class RivalsMetaClient(Protocol):
    def search_player(self, player_name: str) -> list[SearchResult]:
        ...

    def fetch_competitive_heroes(self, profile_url: str) -> tuple[HeroStat, ...]:
        ...


class HttpRivalsMetaClient:
    def __init__(self, base_url: str = "https://rivalsmeta.com", timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": "MarvelRivalsBanHelper/0.1 personal-local-mvp"},
        )

    def search_player(self, player_name: str) -> list[SearchResult]:
        normalized = normalize_player_name(player_name)
        if not normalized or is_hidden_streamer_name(normalized):
            return []

        # RivalsMeta does not currently advertise a public API. Keep this URL
        # construction isolated so a browser-inspected route can replace it.
        response = self._client.get(f"{self.base_url}/search", params={"q": normalized})
        response.raise_for_status()
        return parse_search_results(response.text, self.base_url)

    def fetch_competitive_heroes(self, profile_url: str) -> tuple[HeroStat, ...]:
        response = self._client.get(profile_url)
        response.raise_for_status()
        return parse_competitive_heroes(response.text)


def select_exact_profile(player_name: str, results: list[SearchResult]) -> SearchResult | None:
    exact_matches = [
        result for result in results if is_exact_profile_match(player_name, result.display_name)
    ]
    if len(exact_matches) != 1:
        return None
    return exact_matches[0]


def lookup_exact_profile(client: RivalsMetaClient, player_name: str) -> PlayerProfile | None:
    normalized = normalize_player_name(player_name)
    if not normalized or is_hidden_streamer_name(normalized):
        return None

    selected = select_exact_profile(normalized, client.search_player(normalized))
    if selected is None:
        return None

    return PlayerProfile(
        requested_name=normalized,
        display_name=selected.display_name,
        profile_url=selected.profile_url,
        competitive_heroes=client.fetch_competitive_heroes(selected.profile_url),
    )


def parse_search_results(html: str, base_url: str) -> list[SearchResult]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[SearchResult] = []

    for anchor in soup.select('a[href*="/player/"]'):
        href = anchor.get("href")
        if not href:
            continue
        display_name = normalize_player_name(anchor.get_text(" ", strip=True))
        if not display_name:
            continue
        profile_url = href if href.startswith("http") else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
        results.append(SearchResult(display_name=display_name, profile_url=profile_url))

    return _dedupe_search_results(results)


def parse_competitive_heroes(html: str) -> tuple[HeroStat, ...]:
    soup = BeautifulSoup(html, "html.parser")
    competitive_section = _find_competitive_section(soup)
    if competitive_section is None:
        competitive_section = soup

    stats: list[HeroStat] = []
    for row in competitive_section.select("[data-hero-stat], tr, li, article, div"):
        hero_name = row.get("data-hero") or row.get("data-hero-name")
        games_text = row.get("data-games") or ""
        win_rate_text = row.get("data-win-rate") or ""
        text = normalize_player_name(row.get_text(" ", strip=True))

        if hero_name is None:
            hero_name = _extract_labeled_value(text, "Hero")
        if not games_text:
            games_text = _extract_labeled_value(text, "Games")
        if not win_rate_text:
            win_rate_text = _extract_labeled_value(text, "Win Rate") or _extract_percent(text)

        parsed_games = _parse_int(games_text)
        parsed_win_rate = _parse_win_rate(win_rate_text)
        normalized_hero = normalize_player_name(hero_name or "")

        if normalized_hero and parsed_games is not None and parsed_win_rate is not None:
            stats.append(
                HeroStat(
                    hero_name=normalized_hero,
                    games_played=parsed_games,
                    win_rate=parsed_win_rate,
                )
            )

    return tuple(_dedupe_hero_stats(stats))


def _find_competitive_section(soup: BeautifulSoup) -> BeautifulSoup | None:
    for candidate in soup.select("[data-mode], section, div"):
        mode = (candidate.get("data-mode") or "").casefold()
        text = candidate.get_text(" ", strip=True).casefold()
        if mode == "competitive" or "competitive" in text:
            return candidate
    return None


def _extract_labeled_value(text: str, label: str) -> str:
    marker = f"{label}:"
    if marker not in text:
        return ""
    return text.split(marker, 1)[1].split("|", 1)[0].strip()


def _extract_percent(text: str) -> str:
    for token in text.split():
        if token.endswith("%"):
            return token
    return ""


def _parse_int(value: str) -> int | None:
    digits = "".join(char for char in value if char.isdigit())
    return int(digits) if digits else None


def _parse_win_rate(value: str) -> float | None:
    stripped = value.strip()
    if not stripped:
        return None
    numeric = stripped.rstrip("%")
    try:
        parsed = float(numeric)
    except ValueError:
        return None
    return parsed / 100 if "%" in stripped or parsed > 1 else parsed


def _dedupe_search_results(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[tuple[str, str]] = set()
    deduped: list[SearchResult] = []
    for result in results:
        key = (result.display_name.casefold(), result.profile_url)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(result)
    return deduped


def _dedupe_hero_stats(stats: list[HeroStat]) -> list[HeroStat]:
    deduped: dict[str, HeroStat] = {}
    for stat in stats:
        deduped.setdefault(stat.hero_name.casefold(), stat)
    return list(deduped.values())


def search_url_for_manual_probe(base_url: str, player_name: str) -> str:
    return f"{base_url.rstrip('/')}/search?q={quote_plus(normalize_player_name(player_name))}"

