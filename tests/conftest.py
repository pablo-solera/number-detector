"""Configuración y fixtures para todos los tests"""

import pytest


@pytest.fixture
def temp_folders(tmp_path):
    """Crea estructura temporal de carpetas para tests"""
    base = tmp_path / "base"
    compare = tmp_path / "compare"
    dest = tmp_path / "dest"

    base.mkdir()
    compare.mkdir()
    dest.mkdir()

    return {"base": base, "compare": compare, "dest": dest, "root": tmp_path}


@pytest.fixture
def sample_files(temp_folders):
    """Crea archivos de ejemplo para tests"""
    base = temp_folders["base"]
    compare = temp_folders["compare"]

    # Archivos en base
    (base / "file1.txt").write_text("content 1")
    (base / "file2.txt").write_text("content 2")
    (base / "subdir").mkdir()
    (base / "subdir" / "file3.txt").write_text("content 3")

    # Archivos en compare (algunos compartidos, algunos nuevos)
    (compare / "file1.txt").write_text("content 1")  # Existe en base
    (compare / "new_file.txt").write_text("new content")  # NUEVO
    (compare / "subdir").mkdir()
    (compare / "subdir" / "new_file2.txt").write_text("new content 2")  # NUEVO

    return temp_folders
