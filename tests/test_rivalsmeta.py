from src.models import HeroStat
from src.rivalsmeta import (
    SearchResult,
    lookup_exact_profile,
    parse_competitive_heroes,
    parse_search_results,
    select_exact_profile,
)


class FakeClient:
    def __init__(
        self,
        results: list[SearchResult],
        heroes: tuple[HeroStat, ...] = (HeroStat("Hela", 12, 0.58),),
    ) -> None:
        self.results = results
        self.heroes = heroes

    def search_player(self, player_name: str) -> list[SearchResult]:
        return self.results

    def fetch_competitive_heroes(self, profile_url: str) -> tuple[HeroStat, ...]:
        return self.heroes


def test_select_exact_profile_accepts_single_exact_match() -> None:
    result = select_exact_profile(
        "Krazzo Xorro",
        [SearchResult(" krazzo  xorro ", "https://rivalsmeta.com/player/1")],
    )

    assert result is not None
    assert result.profile_url.endswith("/1")


def test_select_exact_profile_rejects_lookalike_match() -> None:
    result = select_exact_profile(
        "gro0ty",
        [SearchResult("grooty", "https://rivalsmeta.com/player/1")],
    )

    assert result is None


def test_select_exact_profile_rejects_ambiguous_exact_matches() -> None:
    result = select_exact_profile(
        "goreix",
        [
            SearchResult("goreix", "https://rivalsmeta.com/player/1"),
            SearchResult("GOREIX", "https://rivalsmeta.com/player/2"),
        ],
    )

    assert result is None


def test_lookup_exact_profile_skips_hidden_names() -> None:
    assert lookup_exact_profile(FakeClient([]), "****2") is None


def test_lookup_exact_profile_returns_profile_for_exact_match() -> None:
    profile = lookup_exact_profile(
        FakeClient([SearchResult("goreix", "https://rivalsmeta.com/player/1")]),
        "goreix",
    )

    assert profile is not None
    assert profile.display_name == "goreix"
    assert profile.competitive_heroes == (HeroStat("Hela", 12, 0.58),)


def test_parse_search_results_extracts_player_links() -> None:
    html = """
    <main>
      <a href="/player/123">goreix</a>
      <a href="/characters">Characters</a>
      <a href="https://rivalsmeta.com/player/456">Krazzo Xorro</a>
    </main>
    """

    results = parse_search_results(html, "https://rivalsmeta.com")

    assert results == [
        SearchResult("goreix", "https://rivalsmeta.com/player/123"),
        SearchResult("Krazzo Xorro", "https://rivalsmeta.com/player/456"),
    ]


def test_parse_competitive_heroes_from_fixture_markup() -> None:
    html = """
    <section data-mode="competitive">
      <div data-hero-stat data-hero="Hela" data-games="24" data-win-rate="58%"></div>
      <div data-hero-stat>
        Hero: Magik | Games: 12 | Win Rate: 62%
      </div>
    </section>
    """

    assert parse_competitive_heroes(html) == (
        HeroStat("Hela", 24, 0.58),
        HeroStat("Magik", 12, 0.62),
    )
