from pathlib import Path
from src import RedNumberDetector, ExcelExporter
import argparse

BASE_DIR = Path(__file__).parent
DEFAULT_INPUT_DIR = BASE_DIR / "input"
DEFAULT_OUTPUT_FILE = BASE_DIR / "output" / "numeros_rojos.xlsx"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Detector de números rojos en esquemas BMW"
    )

    parser.add_argument(
        "-i", "--input",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Directorio con imágenes a procesar (por defecto: {DEFAULT_INPUT_DIR})"
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help=f"Archivo Excel de salida (por defecto: {DEFAULT_OUTPUT_FILE})"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Guardar imágenes de debug"
    )

    return parser.parse_args()


def main():
    args = parse_args()

    input_dir = args.input
    output_file = args.output
    debug = args.debug

    output_dir = output_file.parent
    debug_dir = output_dir / "debug"

    output_dir.mkdir(parents=True, exist_ok=True)
    if debug:
        debug_dir.mkdir(parents=True, exist_ok=True)

    detector = RedNumberDetector(
        debug=debug,
        debug_dir=debug_dir if debug else None
    )

    exporter = ExcelExporter(output_file)
    rows = []

    for image_path in input_dir.iterdir():
        if image_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        numbers, motors = detector.process(image_path)

        if not motors:
            motors = [""]

        motor_str = ", ".join(motors)

        for number in numbers:
            rows.append([
                image_path.stem,
                number,
                motor_str
            ])

    exporter.export(rows)

    print(f"\n{'='*60}")
    print(f"✓ Excel generado correctamente en {output_file}")
    print(f"📊 Total de filas generadas: {len(rows)}")
    if debug:
        print(f"🔍 Imágenes de debug en {debug_dir}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()