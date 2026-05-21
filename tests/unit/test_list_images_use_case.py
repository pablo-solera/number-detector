from number_detector.application.use_cases.list_images_use_case import ListImagesUseCase


def test_list_images_returns_supported_files_sorted(temp_folders) -> None:
    folder = temp_folders["base"]
    (folder / "b.JPG").write_text("image")
    (folder / "a.png").write_text("image")
    (folder / "notes.txt").write_text("text")
    (folder / "nested").mkdir()
    (folder / "nested" / "c.png").write_text("image")

    result = ListImagesUseCase().execute(folder)

    assert [path.name for path in result.images] == ["a.png", "b.JPG"]


def test_list_images_returns_empty_for_missing_folder(temp_folders) -> None:
    result = ListImagesUseCase().execute(temp_folders["base"] / "missing")

    assert result.images == []
