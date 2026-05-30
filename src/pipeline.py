from __future__ import annotations

from pathlib import Path

from src.models import PipelineResult
from src.name_matching import is_hidden_streamer_name
from src.ocr import OcrEngine, extract_enemy_names_from_image
from src.rivalsmeta import RivalsMetaClient, lookup_exact_profile
from src.scoring import recommend_bans


def run_pipeline(
    image_path: str | Path,
    *,
    ocr_engine: OcrEngine,
    rivalsmeta_client: RivalsMetaClient,
) -> PipelineResult:
    extracted_names = extract_enemy_names_from_image(image_path, ocr_engine)
    matched_profiles = []
    skipped_names = []

    for name in extracted_names:
        if is_hidden_streamer_name(name):
            skipped_names.append(name)
            continue

        profile = lookup_exact_profile(rivalsmeta_client, name)
        if profile is None:
            skipped_names.append(name)
            continue

        matched_profiles.append(profile)

    recommendations = recommend_bans(tuple(matched_profiles))
    return PipelineResult(
        extracted_names=extracted_names,
        matched_profiles=tuple(matched_profiles),
        skipped_names=tuple(skipped_names),
        recommendations=recommendations,
    )

