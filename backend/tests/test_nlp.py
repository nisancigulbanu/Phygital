import pytest

from backend.services.nlp_parser import parse_label_text


@pytest.mark.parametrize(
    "text,expected",
    [
        ("100% Cotton", {"pamuk": 100}),
        ("%80 Pamuk %20 Polyester", {"pamuk": 80, "polyester": 20}),
        ("80% Baumwolle 20% Polyester", {"pamuk": 80, "polyester": 20}),
        ("Cotton %70 Polyester %30", {"pamuk": 70, "polyester": 30}),
        ("57% viskoz 31% poliamit 12% keten", {"viskon": 57, "naylon": 31, "keten": 12}),
        ("57% viskozu 31% poliamidi 12% keten", {"viskon": 57, "naylon": 31, "keten": 12}),
    ],
)
def test_fabric_parsing(text, expected):
    result = parse_label_text(text)
    assert result["fabric_composition"] == {key: float(value) for key, value in expected.items()}
