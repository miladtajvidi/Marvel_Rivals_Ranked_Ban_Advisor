from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from PIL import Image, ImageEnhance, ImageOps

from src.name_matching import is_hidden_streamer_name, normalize_player_name


@dataclass(frozen=True)
class OcrLine:
    text: str
    confidence: float


class OcrEngine(Protocol):
    def read_lines(self, image: Image.Image) -> list[OcrLine]:
        ...


class UnconfiguredOcrEngine:
    def read_lines(self, image: Image.Image) -> list[OcrLine]:
        raise RuntimeError(
            "No local OCR engine is configured. Install the optional OCR dependency "
            "and wire an engine adapter before running screenshot extraction."
        )


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    oriented = ImageOps.exif_transpose(image)
    if oriented.width > 1800 or oriented.height > 1800:
        return oriented.resize((oriented.width // 2, oriented.height // 2))

    return ImageEnhance.Contrast(oriented.convert("L")).enhance(1.4)


def extract_enemy_names_from_image(
    image_path: str | Path,
    engine: OcrEngine,
    *,
    min_confidence: float = 0.65,
    max_names: int = 6,
) -> tuple[str, ...]:
    image = Image.open(image_path)
    return extract_enemy_names(ImageOps.exif_transpose(image), engine, min_confidence=min_confidence)[
        :max_names
    ]


def extract_enemy_names(
    image: Image.Image,
    engine: OcrEngine,
    *,
    min_confidence: float = 0.65,
) -> tuple[str, ...]:
    processed = preprocess_for_ocr(image)
    lines = engine.read_lines(processed)
    return postprocess_ocr_lines(lines, min_confidence=min_confidence)


def postprocess_ocr_lines(
    lines: list[OcrLine],
    *,
    min_confidence: float = 0.65,
) -> tuple[str, ...]:
    names: list[str] = []
    for line in lines:
        if line.confidence < min_confidence:
            continue
        candidate = normalize_player_name(line.text)
        if is_hidden_streamer_name(candidate):
            names.append(candidate)
            continue
        if not candidate or _is_ui_noise(candidate):
            continue
        names.append(candidate)

    return tuple(_dedupe_preserve_order(names))


def _is_ui_noise(text: str) -> bool:
    normalized = text.casefold()
    normalized_letters = "".join(char for char in normalized if char.isalpha())
    if normalized in {"enemy team", "team", "enemy"}:
        return True
    if normalized_letters in {"enemyteam", "enemvtem", "enemvytem", "enemytem", "enemyteem"}:
        return True
    if len(normalized) < 3:
        return True
    if not any(char.isalpha() for char in normalized):
        return True
    return False


def _dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(value)
    return deduped
