from backend.utils.fabric_parser import extract_fabrics_from_text


def test_extract_fabrics_includes_polyamide():
    result = extract_fabrics_from_text("%84 Viskon %16 Polyamid")
    assert result == {"viscose": 84, "polyamide": 16}


def test_extract_fabrics_keeps_multi_word_materials():
    result = extract_fabrics_from_text("%95 Organic Cotton %5 Elastane")
    assert result == {"organic cotton": 95, "elastane": 5}


def test_extract_fabrics_supports_turkish_characters():
    result = extract_fabrics_from_text("49% polyester, 30% yün, 21% akrilik")
    assert result == {"polyester": 49, "wool": 30, "acrylic": 21}


def test_extract_fabrics_supports_turkish_product_wording():
    result = extract_fabrics_from_text("57% viskoz 31% poliamit 12% keten")
    assert result == {"viscose": 57, "polyamide": 31, "linen": 12}


def test_extract_fabrics_ignores_unknown_percentage_phrases():
    result = extract_fabrics_from_text("Sepette %50 indirim, %100 orijinal urun, %80 Viskon %20 Polyamid")
    assert result == {"viscose": 80, "polyamide": 20}


def test_extract_fabrics_supports_inflected_words():
    result = extract_fabrics_from_text("57% viskozu 31% poliamidi 12% keten")
    assert result == {"viscose": 57, "polyamide": 31, "linen": 12}
