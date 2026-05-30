from __future__ import annotations

import math
from collections import defaultdict

from src.models import BanRecommendation, PlayerProfile


def hero_score(games_played: int, win_rate: float) -> float:
    if games_played <= 0:
        return 0.0

    sample_weight = math.log1p(games_played)
    performance_weight = max(win_rate - 0.45, 0.05)
    return sample_weight * performance_weight


def recommend_bans(
    profiles: list[PlayerProfile] | tuple[PlayerProfile, ...],
    *,
    limit: int = 2,
    min_games: int = 3,
) -> tuple[BanRecommendation, ...]:
    hero_scores: dict[str, float] = defaultdict(float)
    hero_games: dict[str, int] = defaultdict(int)
    hero_players: dict[str, set[str]] = defaultdict(set)

    for profile in profiles:
        for hero in profile.competitive_heroes:
            if hero.games_played < min_games:
                continue

            hero_scores[hero.hero_name] += hero_score(hero.games_played, hero.win_rate)
            hero_games[hero.hero_name] += hero.games_played
            hero_players[hero.hero_name].add(profile.display_name)

    ranked = sorted(
        hero_scores,
        key=lambda hero_name: (
            hero_scores[hero_name],
            len(hero_players[hero_name]),
            hero_games[hero_name],
            hero_name.casefold(),
        ),
        reverse=True,
    )

    return tuple(
        BanRecommendation(
            hero_name=hero_name,
            score=hero_scores[hero_name],
            contributing_players=tuple(sorted(hero_players[hero_name])),
            total_games=hero_games[hero_name],
        )
        for hero_name in ranked[:limit]
    )

