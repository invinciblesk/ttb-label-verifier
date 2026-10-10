from main import (
    REQUIRED_WARNING,
    normalize_text,
    verify_alcohol,
    verify_government_warning,
    verify_net_contents,
    verify_optional_text_field,
    verify_text_field,
)


def test_normalization_ignores_case_and_punctuation():
    assert normalize_text("STONE'S THROW") == normalize_text("Stone's Throw")


def test_brand_name_match():
    result = verify_text_field(
        "Brand Name",
        "OLD TOM DISTILLERY",
        "OLD TOM DISTILLERY"
    )

    assert result["status"] == "PASS"
    assert result["similarity"] == 100


def test_brand_name_case_and_punctuation_match():
    result = verify_text_field(
        "Brand Name",
        "STONE'S THROW",
        "Stone's Throw"
    )

    assert result["status"] == "PASS"


def test_alcohol_content_match():
    result = verify_alcohol(
        "45%",
        "Kentucky Bourbon\n45% Alc./Vol. (90 Proof)\n750 mL"
    )

    assert result["status"] == "PASS"


def test_alcohol_content_mismatch():
    result = verify_alcohol(
        "45%",
        "GIN\n50% ALC/VOL\n750 ML"
    )

    assert result["status"] == "FAIL"


def test_net_contents_match():
    result = verify_net_contents(
        "750 mL",
        "GIN\n50% ALC/VOL\n750 ML"
    )

    assert result["status"] == "PASS"


def test_government_warning_match():
    result = verify_government_warning(REQUIRED_WARNING)

    assert result["status"] == "PASS"


def test_missing_government_warning_fails():
    result = verify_government_warning(
        "OLD TOM DISTILLERY\n45% Alc./Vol.\n750 mL"
    )

    assert result["status"] == "FAIL"


def test_producer_can_match_inside_longer_line():
    result = verify_optional_text_field(
        "Producer / Bottler",
        "Old Tom Distillery",
        "Produced and Bottled by Old Tom Distillery"
    )

    assert result["status"] == "PASS"


def test_country_can_match_inside_longer_line():
    result = verify_optional_text_field(
        "Country of Origin",
        "United States",
        "Louisville, Kentucky, United States"
    )

    assert result["status"] == "PASS"
