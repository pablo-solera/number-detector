from number_detector.domain.parsing import extract_motor_codes, extract_part_numbers, normalize_motor_text


def test_extract_part_numbers_filters_by_digit_length() -> None:
    assert extract_part_numbers("12 123 123456 1234567 abc 123") == [123, 123456]


def test_normalize_motor_text_removes_common_ocr_spacing_noise() -> None:
    assert normalize_motor_text(" 1.5 / B38A15P\t") == "1.5/B38A15P"


def test_extract_motor_codes_returns_unique_sorted_codes() -> None:
    assert extract_motor_codes("1.5/B38A15P KW: 1.5/B38A15P /ZKU-ZK02") == [
        "/ZKU-ZK02",
        "1.5/B38A15P",
    ]


def test_extract_motor_codes_ignores_blue_motor_metadata() -> None:
    assert extract_motor_codes("1.4/DGEA\nkw:110/Cv:150\nidVeic:1025397") == ["1.4/DGEA"]
