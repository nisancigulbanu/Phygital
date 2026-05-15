from backend.services.ocr_service import _resolve_tesseract_languages


class _FakeFile:
    def __init__(self, stem: str):
        self.stem = stem


class _FakeTessdataDir:
    def __init__(self, stems: list[str]):
        self._stems = stems

    def glob(self, pattern: str):
        return [_FakeFile(stem) for stem in self._stems]


def test_resolve_tesseract_languages_prefers_turkish_and_english():
    assert _resolve_tesseract_languages(_FakeTessdataDir(["tur", "eng"])) == "tur+eng"


def test_resolve_tesseract_languages_falls_back_to_english():
    assert _resolve_tesseract_languages(_FakeTessdataDir(["osd"])) == "eng"
