"""Rule tables for textile quality scoring."""

FABRIC_QUALITY_SCORES = {
    "ipek": 95,
    "kasmir": 98,
    "yun": 82,
    "merinos": 90,
    "keten": 78,
    "pamuk": 72,
    "organik pamuk": 85,
    "pima pamuk": 88,
    "viskon": 58,
    "modal": 65,
    "lyocell": 70,
    "bambu": 63,
    "polyester": 35,
    "naylon": 40,
    "akrilik": 28,
    "elastan": 45,
    "geri donusturulmus polyester": 52,
    "geri donusturulmus naylon": 55,
}

ORIGIN_BONUS = {
    "Italy": 8,
    "Japan": 7,
    "Portugal": 6,
    "Germany": 5,
    "France": 5,
    "Turkey": 4,
    "India": 2,
    "Bangladesh": 0,
    "China": 1,
    "Vietnam": 0,
    "Cambodia": 0,
}
