"""Tests para FileService"""

from pathlib import Path



from number_detector.application.use_cases.scan_single_image_use_case import ScanSingleImageUseCase


class TestScanSingleImageUseCase:
    """Tests del servicio de archivos"""

    def __init__(self):
        self.use_case = ScanSingleImageUseCase

    def test_image_not_provided(self, temp_folders):
        """Test que walk_files retorna todos los archivos"""
        folder = temp_folders["base"]
        image = None

        # Crear estructura de archivos
        (folder / "file1.txt").write_text("1")
        (folder / "file2.txt").write_text("2")
        (folder / "subdir").mkdir()
        (folder / "subdir" / "file3.txt").write_text("3")

        files = list(FileService.walk_files(folder))

        assert len(files) == 3
        assert all(isinstance(f, Path) for f in files)
        assert all(f.is_file() for f in files)

    def test_walk_files_empty_directory(self, temp_folders):
        """Test walk_files con directorio vacío"""
        files = list(FileService.walk_files(temp_folders["base"]))

        assert len(files) == 0

    def test_walk_files_ignores_directories(self, temp_folders):
        """Test que walk_files ignora directorios"""
        folder = temp_folders["base"]

        (folder / "dir1").mkdir()
        (folder / "dir2").mkdir()
        (folder / "file.txt").write_text("content")

        files = list(FileService.walk_files(folder))

        assert len(files) == 1
        assert files[0].name == "file.txt"

    def test_copy_file_simple(self, temp_folders):
        """Test copia simple de archivo"""
        source = temp_folders["base"] / "source.txt"
        source.write_text("test content")

        dest = temp_folders["dest"] / "copy.txt"

        FileService.copy_file(source, dest)

        assert dest.exists()
        assert dest.read_text() == "test content"

    def test_copy_file_creates_parent_dirs(self, temp_folders):
        """Test que copy_file crea directorios padres"""
        source = temp_folders["base"] / "source.txt"
        source.write_text("content")

        dest = temp_folders["dest"] / "a" / "b" / "c" / "file.txt"

        FileService.copy_file(source, dest)

        assert dest.exists()
        assert dest.parent.exists()

    def test_copy_file_preserves_metadata(self, temp_folders):
        """Test que copy_file preserva metadata"""
        source = temp_folders["base"] / "source.txt"
        source.write_text("content")

        original_stat = source.stat()

        dest = temp_folders["dest"] / "copy.txt"
        FileService.copy_file(source, dest)

        # shutil.copy2 preserva timestamps
        assert abs(dest.stat().st_mtime - original_stat.st_mtime) < 0.1
