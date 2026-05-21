"""Tests para LoggerService"""

from folder_comparison.models.comparison_result import FileOperation
from folder_comparison.services.logger_service import LoggerService


class TestLoggerService:
    """Tests del servicio de logging"""

    def test_save_log_creates_file(self, temp_folders):
        """Test que save_log crea archivo de log"""
        operations = [
            FileOperation("file1.txt", "copied", "✓ Copiado: file1.txt"),
            FileOperation("file2.txt", "skipped", "⊘ Ignorado: file2.txt"),
        ]

        log_path = temp_folders["dest"] / "test.log"

        result_path = LoggerService.save_log(log_path, operations)

        assert result_path == log_path
        assert log_path.exists()

    def test_save_log_content(self, temp_folders):
        """Test contenido del log"""
        operations = [
            FileOperation("file1.txt", "copied", "✓ Copiado: file1.txt"),
            FileOperation("file2.txt", "skipped", "⊘ Ignorado: file2.txt"),
        ]

        log_path = temp_folders["dest"] / "test.log"
        LoggerService.save_log(log_path, operations)

        content = log_path.read_text(encoding="utf-8")

        assert "✓ Copiado: file1.txt" in content
        assert "⊘ Ignorado: file2.txt" in content

    def test_save_log_empty_operations(self, temp_folders):
        """Test log con lista vacía de operaciones"""
        log_path = temp_folders["dest"] / "empty.log"

        LoggerService.save_log(log_path, [])

        assert log_path.exists()
        assert log_path.read_text() == ""
