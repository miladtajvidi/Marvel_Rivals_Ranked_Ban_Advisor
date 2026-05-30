from __future__ import annotations

from PIL import Image

from src.ocr import OcrLine


class EasyOcrEngine:
    def __init__(self, languages: list[str] | None = None) -> None:
        try:
            import easyocr
        except ImportError as exc:
            raise RuntimeError(
                "EasyOCR is not installed. Install OCR extras with "
                "`pip install -e .[ocr]` before running the app."
            ) from exc

        self._reader = easyocr.Reader(languages or ["en"], gpu=False)

    def read_lines(self, image: Image.Image) -> list[OcrLine]:
        import numpy as np

        results = self._reader.readtext(np.array(image))
        return [OcrLine(text=text, confidence=float(confidence)) for _, text, confidence in results]


def create_default_ocr_engine() -> EasyOcrEngine:
    return EasyOcrEngine()
