from pathlib import Path
from src import RedNumberDetector, ExcelExporter
import time

BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
DEBUG_DIR = OUTPUT_DIR / "debug"
OUTPUT_FILE = OUTPUT_DIR / "numeros_rojos.xlsx"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Obtener todas las imagenes
    image_paths = []
    for ext in [".jpg", ".jpeg", ".png"]:
        image_paths.extend(INPUT_DIR.glob(f"*{ext}"))

    if not image_paths:
        print("No se encontraron imagenes en input/")
        return

    print(f"\nTotal de imagenes encontradas: {len(image_paths)}")

    # Crear detector
    detector = RedNumberDetector(debug=False, debug_dir=DEBUG_DIR)

    # Procesar en paralelo
    start_time = time.time()

    # max_workers=None usa todos los CPUs disponibles
    # Puedes ajustar a un numero especifico: max_workers=4
    results = detector.process_batch(image_paths, max_workers=None)

    elapsed_time = time.time() - start_time

    # Preparar datos para Excel
    rows = []
    for image_path, (numbers, motors) in results.items():
        if not motors:
            motors = [""]

        for number in numbers:
            for motor in motors:
                rows.append([
                    image_path.stem,
                    number,
                    motor
                ])

    # Exportar a Excel
    exporter = ExcelExporter(OUTPUT_FILE)
    exporter.export(rows)

    print(f"\n{'=' * 70}")
    print(f"RESUMEN FINAL")
    print(f"{'=' * 70}")
    print(f"Tiempo total: {elapsed_time:.2f} segundos")
    print(f"Imagenes procesadas: {len(results)}")
    print(f"Tiempo promedio por imagen: {elapsed_time / len(results):.2f}s")
    print(f"Filas generadas en Excel: {len(rows)}")
    print(f"Excel generado: {OUTPUT_FILE}")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()