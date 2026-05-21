from pathlib import Path

import pytest

from number_detector.application.settings import DetectionSettings
from number_detector.infrastructure.bootstrap import create_scan_single_image_use_case
from number_detector.infrastructure.runtime import check_tesseract_installed


@pytest.mark.skipif(not check_tesseract_installed(), reason="Tesseract is not available")
def test_detects_red_numbers_from_etka_sample() -> None:
    image_path = Path("tests/fixtures/test4.jpg")
    expected = {
        7571,
        1966,
        1772,
        7082,
        8084,
        4124,
        9654,
        1972,
        2228,
        5502,
        5733,
        2050,
        2304,
        3911,
        8571,
        8572,
    }

    result = create_scan_single_image_use_case(DetectionSettings()).execute(image_path)

    assert result.error is None
    assert expected.issubset(set(result.part_numbers))


@pytest.mark.skipif(not check_tesseract_installed(), reason="Tesseract is not available")
def test_detects_two_digit_red_number_from_etka_sample() -> None:
    result = create_scan_single_image_use_case(DetectionSettings()).execute(Path("tests/fixtures/test3.jpg"))

    assert result.error is None
    assert 47 in result.part_numbers


@pytest.mark.skipif(not check_tesseract_installed(), reason="Tesseract is not available")
def test_detects_blue_motor_code_from_etka_sample() -> None:
    result = create_scan_single_image_use_case(DetectionSettings()).execute(Path("tests/fixtures/test1.jpg"))

    assert result.error is None
    assert any("1.4/DGEA" in text for text in result.motor_codes)
    assert any("kw:110" in text for text in result.motor_codes)
    assert any("idVeic" in text for text in result.motor_codes)


@pytest.mark.skipif(not check_tesseract_installed(), reason="Tesseract is not available")
def test_detects_green_free_text_from_etka_sample() -> None:
    result = create_scan_single_image_use_case(DetectionSettings()).execute(Path("tests/fixtures/test1.jpg"))

    assert result.error is None
    assert "Plug-in Hybrid" in result.free_text


@pytest.mark.skipif(not check_tesseract_installed(), reason="Tesseract is not available")
def test_detects_pink_body_text_from_etka_samples() -> None:
    test2 = create_scan_single_image_use_case(DetectionSettings()).execute(Path("tests/fixtures/test2.jpg"))
    test4 = create_scan_single_image_use_case(DetectionSettings()).execute(Path("tests/fixtures/test4.jpg"))

    assert test2.error is None
    assert any("CD1" in text for text in test2.body_text)
    assert any("Berlina" in text for text in test2.body_text)
    assert test4.error is None
    assert any("Station Wagon" in text for text in test4.body_text)
