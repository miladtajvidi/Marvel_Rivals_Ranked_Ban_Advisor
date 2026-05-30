from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class HeroStat:
    hero_name: str
    games_played: int
    win_rate: float


@dataclass(frozen=True)
class PlayerProfile:
    requested_name: str
    display_name: str
    profile_url: str
    competitive_heroes: tuple[HeroStat, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BanRecommendation:
    hero_name: str
    score: float
    contributing_players: tuple[str, ...]
    total_games: int


@dataclass(frozen=True)
class PipelineResult:
    extracted_names: tuple[str, ...]
    matched_profiles: tuple[PlayerProfile, ...]
    skipped_names: tuple[str, ...]
    recommendations: tuple[BanRecommendation, ...]

