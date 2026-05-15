from __future__ import annotations

import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import numpy as np

try:  # pragma: no cover - optional dependency
    import cv2
except ImportError:  # pragma: no cover
    cv2 = None

try:  # pragma: no cover - optional dependency
    import pytesseract
except ImportError:  # pragma: no cover
    pytesseract = None


logger = logging.getLogger(__name__)
DEFAULT_TESSERACT_CANDIDATES = (
    shutil.which("tesseract"),
    r"C:\msys64\ucrt64\bin\tesseract.exe",
)
DEFAULT_TESSDATA_CANDIDATES = (
    Path(r"C:\msys64\ucrt64\share\tessdata"),
    Path(r"C:\Program Files\Tesseract-OCR\tessdata"),
)


class OCRServiceError(RuntimeError):
    """Raised when no OCR provider can extract usable text."""


def preprocess_image(img_bytes: bytes) -> np.ndarray | None:
    """Prepare an image for OCR when OpenCV is available."""
    if cv2 is None:
        return None
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return cv2.fastNlMeansDenoising(enhanced, h=10)


def extract_text(image_bytes: bytes, settings) -> dict[str, str | float]:
    """Extract raw text from image bytes using demo, Tesseract, or a text fallback."""
    demo_text = _decode_text_payload(image_bytes)
    if demo_text:
        return {"raw_text": demo_text, "confidence": 0.99, "provider": "demo_text"}

    if pytesseract is not None:
        processed = preprocess_image(image_bytes)
        if processed is not None:
            best_result = _run_tesseract_candidates(processed)
            if best_result is not None:
                logger.info("OCR tamamlandi: provider=tesseract")
                return best_result

    cli_result = _run_tesseract_cli(image_bytes)
    if cli_result is not None:
        logger.info("OCR tamamlandi: provider=tesseract_cli")
        return cli_result

    raise OCRServiceError("ocr_failed")


def _decode_text_payload(image_bytes: bytes) -> str:
    """Allow plain UTF-8 text bytes as a deterministic demo OCR input."""
    try:
        text = image_bytes.decode("utf-8").strip()
    except UnicodeDecodeError:
        return ""
    if any(char.isalpha() for char in text):
        return text
    return ""


def _run_tesseract_candidates(image: np.ndarray) -> dict[str, str | float] | None:
    variants = [image]
    if cv2 is not None:
        variants.append(cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1])
        variants.append(cv2.resize(image, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_CUBIC))

    best: dict[str, str | float] | None = None
    best_score = -1.0
    for variant in variants:
        for config in ("--psm 6", "--psm 11"):
            try:
                raw_text = pytesseract.image_to_string(variant, lang="tur+eng", config=config).strip()
            except Exception:
                continue
            if not raw_text:
                continue
            score = _score_ocr_text(raw_text)
            if score > best_score:
                best_score = score
                best = {
                    "raw_text": raw_text,
                    "confidence": min(0.99, round(0.45 + (score / 40), 2)),
                    "provider": "tesseract",
                }
    return best


def _run_tesseract_cli(image_bytes: bytes) -> dict[str, str | float] | None:
    executable = _find_tesseract_executable()
    if executable is None:
        return None

    env = os.environ.copy()
    tessdata_dir = _find_tessdata_dir()
    languages = _resolve_tesseract_languages(tessdata_dir)
    if tessdata_dir is not None:
        env["TESSDATA_PREFIX"] = str(tessdata_dir)

    suffix = ".png"
    input_path = ""
    processed = preprocess_image(image_bytes)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            input_path = temp_file.name
            if processed is not None and cv2 is not None:
                cv2.imwrite(input_path, processed)
            else:
                temp_file.write(image_bytes)

        best: dict[str, str | float] | None = None
        best_score = -1.0
        for config in ("--psm 6", "--psm 11"):
            command = [executable, input_path, "stdout", "-l", languages, *config.split()]
            try:
                completed = subprocess.run(
                    command,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=30,
                    env=env,
                )
            except Exception:
                continue
            raw_text = completed.stdout.strip()
            if not raw_text:
                continue
            score = _score_ocr_text(raw_text)
            if score > best_score:
                best_score = score
                best = {
                    "raw_text": raw_text,
                    "confidence": min(0.99, round(0.45 + (score / 40), 2)),
                    "provider": "tesseract_cli",
                }
        return best
    finally:
        if input_path:
            try:
                Path(input_path).unlink(missing_ok=True)
            except Exception:
                pass


def _find_tesseract_executable() -> str | None:
    for candidate in DEFAULT_TESSERACT_CANDIDATES:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def _find_tessdata_dir() -> Path | None:
    env_path = os.environ.get("TESSDATA_PREFIX", "").strip()
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return candidate
    for candidate in DEFAULT_TESSDATA_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _resolve_tesseract_languages(tessdata_dir: Path | None) -> str:
    if tessdata_dir is None:
        return "eng"
    available = {path.stem.lower() for path in tessdata_dir.glob("*.traineddata")}
    preferred = [language for language in ("tur", "eng") if language in available]
    if preferred:
        return "+".join(preferred)
    return "eng"


def _score_ocr_text(text: str) -> float:
    percentages = len(re.findall(r"\d{1,3}\s*%|%\s*\d{1,3}", text))
    letters = sum(1 for char in text if char.isalpha())
    newlines = text.count("\n")
    return (percentages * 10) + min(letters / 8, 12) + min(newlines, 4)
