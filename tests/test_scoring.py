from src.models import HeroStat, PlayerProfile
from src.scoring import recommend_bans


def profile(name: str, heroes: list[HeroStat]) -> PlayerProfile:
    return PlayerProfile(
        requested_name=name,
        display_name=name,
        profile_url=f"https://example.test/{name}",
        competitive_heroes=tuple(heroes),
    )


def test_empty_profiles_return_no_recommendations() -> None:
    assert recommend_bans([]) == ()


def test_tiny_perfect_sample_is_ignored_by_min_games() -> None:
    recommendations = recommend_bans(
        [
            profile("one", [HeroStat("Hela", 1, 1.0)]),
            profile("two", [HeroStat("Magik", 20, 0.55)]),
        ],
        min_games=3,
    )

    assert [rec.hero_name for rec in recommendations] == ["Magik"]


def test_aggregation_boosts_heroes_across_players() -> None:
    recommendations = recommend_bans(
        [
            profile("one", [HeroStat("Hela", 12, 0.55), HeroStat("Magik", 30, 0.56)]),
            profile("two", [HeroStat("Hela", 12, 0.55)]),
        ],
        min_games=3,
    )

    assert recommendations[0].hero_name == "Hela"
    assert recommendations[0].total_games == 24
    assert recommendations[0].contributing_players == ("one", "two")
