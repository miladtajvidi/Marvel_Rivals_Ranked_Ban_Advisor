from src.models import HeroStat
from src.rivalsmeta_browser import (
    VisiblePlayerResult,
    parse_visible_competitive_heroes,
    select_exact_visible_results,
)


def test_select_exact_visible_results_accepts_one_exact_match() -> None:
    results = select_exact_visible_results(
        "goreix",
        [
            VisiblePlayerResult("Goreilla73", "/player/1"),
            VisiblePlayerResult("goreix", "/player/2"),
        ],
    )

    assert results == [VisiblePlayerResult("goreix", "/player/2")]


def test_select_exact_visible_results_rejects_ambiguous_matches() -> None:
    results = select_exact_visible_results(
        "goreix",
        [
            VisiblePlayerResult("goreix", "/player/1"),
            VisiblePlayerResult("GOREIX", "/player/2"),
        ],
    )

    assert results == []


def test_select_exact_visible_results_rejects_lookalikes() -> None:
    results = select_exact_visible_results(
        "Krazzo Xoro",
        [VisiblePlayerResult("Krazzo Xorro", "/player/1")],
    )

    assert results == []


def test_parse_visible_competitive_heroes_extracts_ranked_rows() -> None:
    text = """
    Profile
    Competitive
    Hela 24 Games 58% Win Rate
    Magik 12 Games 62.5% Win Rate
    Quick Play
    Groot 99 Games 99% Win Rate
    """

    assert parse_visible_competitive_heroes(text) == (
        HeroStat("Hela", 24, 0.58),
        HeroStat("Magik", 12, 0.625),
    )


def test_parse_visible_competitive_heroes_extracts_rivalsmeta_top_hero_order() -> None:
    text = """
    v3rteegoTTV
    Top Heroes
    Competitive
    The Punisher
    3.06 KDA
    27.5/9/0
    50%
    4 games
    Quick Play
    Hela 99 Games 99% Win Rate
    """

    assert parse_visible_competitive_heroes(text) == (
        HeroStat("The Punisher", 4, 0.5),
    )


def test_parse_visible_competitive_heroes_extracts_compact_rendered_text() -> None:
    text = (
        "Top HeroesCompetitiveQuick PlayThe Punisher3.06 KDA27.5/9/050%4 games"
        "Teammates6est9osition6950%4 games"
    )

    assert parse_visible_competitive_heroes(text) == (
        HeroStat("The Punisher", 4, 0.5),
    )
