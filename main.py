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

        numbers, motors = detector.process(image_path)  # Ahora motors es una lista

        # Si no se detectaron motores, usar lista con "N/A"
        if not motors:
            motors = ["N/A"]

        # Generar una fila por cada combinación de número y motor
        for number in numbers:
            for motor in motors:
                rows.append([
                    image_path.name.split(".")[0],
                    number,
                    motor
                ])

    exporter.export(rows)
    print(f"\n{'='*60}")
    print(f"✓ Excel generado correctamente en {OUTPUT_FILE}")
    print(f"📊 Total de filas generadas: {len(rows)}")
    print(f"🔍 Imágenes de debug en {DEBUG_DIR}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()