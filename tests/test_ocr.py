from src.ocr import OcrLine, postprocess_ocr_lines


def test_postprocess_removes_ui_noise_and_low_confidence_lines() -> None:
    result = postprocess_ocr_lines(
        [
            OcrLine("ENEMY TEAM", 0.99),
            OcrLine("goreix", 0.92),
            OcrLine("monitor icon", 0.20),
            OcrLine("Krazzo   Xorro", 0.88),
        ],
        min_confidence=0.65,
    )

    assert result == ("goreix", "Krazzo Xorro")


def test_postprocess_preserves_hidden_names_for_pipeline_skip() -> None:
    result = postprocess_ocr_lines([OcrLine("****2", 0.95)])

    assert result == ("****2",)


def test_postprocess_dedupes_repeated_ocr_lines() -> None:
    result = postprocess_ocr_lines([OcrLine("goreix", 0.9), OcrLine("GOREIX", 0.9)])

    assert result == ("goreix",)


def test_postprocess_discards_title_variants_and_single_digit_artifacts() -> None:
    result = postprocess_ocr_lines(
        [
            OcrLine("ENEMVY TEM", 0.8),
            OcrLine("goreix", 0.9),
            OcrLine("5", 0.9),
            OcrLine("ChoosMcGoose", 0.9),
        ]
    )

    assert result == ("goreix", "ChoosMcGoose")
