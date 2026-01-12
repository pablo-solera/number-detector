from pathlib import Path
from src import RedNumberDetector, ExcelExporter

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
DEBUG_DIR = OUTPUT_DIR / "debug"
OUTPUT_FILE = OUTPUT_DIR / "numeros_rojos.xlsx"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    detector = RedNumberDetector(
        debug=True,
        debug_dir=DEBUG_DIR
    )
    exporter = ExcelExporter(OUTPUT_FILE)

    rows = []

    for image_path in INPUT_DIR.iterdir():
        if image_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        numbers, motor = detector.process(image_path)

        for number in numbers:
            rows.append([
                image_path.name,
                number,
                motor
            ])

    exporter.export(rows)
    print(f"Excel generado correctamente en {OUTPUT_FILE}")
    print(f"Imágenes de debug en {DEBUG_DIR}")


if __name__ == "__main__":
    main()
