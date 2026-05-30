from pathlib import Path

from PIL import Image

from src.models import HeroStat
from src.ocr import OcrLine
from src.pipeline import run_pipeline
from src.rivalsmeta import SearchResult


class FakeOcr:
    def read_lines(self, image: Image.Image) -> list[OcrLine]:
        return [
            OcrLine("goreix", 0.95),
            OcrLine("****2", 0.95),
            OcrLine("gro0ty", 0.95),
            OcrLine("Krazzo Xorro", 0.95),
        ]


class FakeRivalsMeta:
    def search_player(self, player_name: str) -> list[SearchResult]:
        if player_name == "goreix":
            return [SearchResult("goreix", "https://rivalsmeta.test/player/1")]
        if player_name == "Krazzo Xorro":
            return [SearchResult("Krazzo Xorro", "https://rivalsmeta.test/player/2")]
        if player_name == "gro0ty":
            return [SearchResult("grooty", "https://rivalsmeta.test/player/3")]
        return []

    def fetch_competitive_heroes(self, profile_url: str) -> tuple[HeroStat, ...]:
        if profile_url.endswith("/1"):
            return (HeroStat("Hela", 20, 0.58),)
        return (HeroStat("Magik", 15, 0.61),)


def test_pipeline_skips_hidden_and_non_exact_matches(tmp_path: Path) -> None:
    image_path = tmp_path / "sample.png"
    Image.new("RGB", (20, 20), "white").save(image_path)

    result = run_pipeline(
        image_path,
        ocr_engine=FakeOcr(),
        rivalsmeta_client=FakeRivalsMeta(),
    )

    assert result.extracted_names == ("goreix", "****2", "gro0ty", "Krazzo Xorro")
    assert [profile.display_name for profile in result.matched_profiles] == [
        "goreix",
        "Krazzo Xorro",
    ]
    assert result.skipped_names == ("****2", "gro0ty")
    assert [recommendation.hero_name for recommendation in result.recommendations] == [
        "Magik",
        "Hela",
    ]
