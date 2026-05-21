from pathlib import Path

from number_detector.application.use_cases.scan_single_image_use_case import ScanSingleImageUseCase
from number_detector.domain.models.bounding_box import BoundingBox
from number_detector.domain.models.image_region import ImageRegion


class FakeImageReader:
    def __init__(self, image):
        self.image = image

    def read(self, image_path):
        return self.image


class FakeDetector:
    def find_part_regions(self, image, name: str = ""):
        return [ImageRegion(BoundingBox(0, 0, 1, 1), "part-1"), ImageRegion(BoundingBox(1, 0, 1, 1), "part-2")]

    def find_motor_regions(self, image, name: str = ""):
        return [ImageRegion(BoundingBox(0, 1, 1, 1), "motor-1")]

    def find_free_text_regions(self, image, name: str = ""):
        return [ImageRegion(BoundingBox(0, 2, 1, 1), "free-text-1")]


class FakeOcr:
    def read_digits(self, image) -> str:
        return {"part-1": "123", "part-2": "123 4567"}[image]

    def read_text(self, image) -> str:
        return "1.5/B38A15P"

    def read_free_text(self, image) -> str:
        return "Plug-in Hybrid"


def test_scan_single_image_uses_injected_dependencies() -> None:
    use_case = ScanSingleImageUseCase(FakeImageReader(image=object()), FakeDetector(), FakeOcr())

    result = use_case.execute(Path("sample.png"))

    assert result.image_name == "sample"
    assert result.part_numbers == [123, 4567]
    assert result.motor_codes == ["1.5/B38A15P"]
    assert result.free_text == ["Plug-in Hybrid"]
    assert result.error is None


def test_scan_single_image_keeps_two_digit_part_numbers() -> None:
    class TwoDigitOcr(FakeOcr):
        def read_digits(self, image) -> str:
            return "47"

    use_case = ScanSingleImageUseCase(FakeImageReader(image=object()), FakeDetector(), TwoDigitOcr())

    result = use_case.execute("sample.png")

    assert result.part_numbers == [47]


def test_scan_single_image_returns_error_when_image_cannot_be_read() -> None:
    use_case = ScanSingleImageUseCase(FakeImageReader(image=None), FakeDetector(), FakeOcr())

    result = use_case.execute("missing.png")

    assert result.image_name == "missing"
    assert result.part_numbers == []
    assert result.motor_codes == []
    assert result.free_text == []
    assert result.error == "No se pudo abrir"
