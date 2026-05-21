from number_detector.application.use_cases.export_excel_use_case import ExportExcelUseCase
from number_detector.domain.models.detection_result import DetectionResult


class FakeExporter:
    def __init__(self):
        self.rows = None
        self.output_path = None

    def export(self, rows, output_path):
        self.rows = rows
        self.output_path = output_path
        return output_path


def test_export_excel_maps_detection_results_to_rows(tmp_path) -> None:
    exporter = FakeExporter()
    output_path = tmp_path / "result.xlsx"
    results = [
        DetectionResult("img-1", [123, 456], ["1.5/B38A15P"]),
        DetectionResult("img-2", [], ["/ZKU-ZK02"]),
        DetectionResult("img-3", [999], [], error="failed"),
    ]

    result_path = ExportExcelUseCase(exporter).execute(results, output_path)

    assert result_path == output_path
    assert exporter.output_path == output_path
    assert exporter.rows == [
        ["img-1", 123, "1.5/B38A15P"],
        ["img-1", 456, "1.5/B38A15P"],
        ["img-2", "", "/ZKU-ZK02"],
    ]
