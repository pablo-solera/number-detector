import sys
from pathlib import Path
from src import RedNumberDetector, ExcelExporter
import config


def main():
    print("=" * 60)
    print("  Detector de Números Rojos en Imágenes")
    print("=" * 60)
    
    # Verificar que existe la carpeta input
    if not config.INPUT_DIR.exists():
        print(f"\n❌ Error: La carpeta '{config.INPUT_DIR}' no existe")
        print(f"   Créala y coloca las imágenes dentro")
        return 1
    
    # Verificar que hay imágenes
    images = list(config.INPUT_DIR.glob('*'))
    images = [img for img in images if img.suffix.lower() in config.IMAGE_EXTENSIONS]
    
    if not images:
        print(f"\n⚠ No se encontraron imágenes en '{config.INPUT_DIR}'")
        print(f"   Extensiones soportadas: {', '.join(config.IMAGE_EXTENSIONS)}")
        return 1
    
    print(f"\n📁 Carpeta de entrada: {config.INPUT_DIR}")
    print(f"📊 Imágenes encontradas: {len(images)}")
    print(f"📂 Carpeta de salida: {config.OUTPUT_DIR}\n")
    
    # Procesar imágenes
    detector = RedNumberDetector()
    results = detector.process_folder(config.INPUT_DIR)
    
    # Exportar resultados
    exporter = ExcelExporter()
    output_path = config.OUTPUT_DIR / config.OUTPUT_FILENAME
    success = exporter.export_to_excel(results, output_path)
    
    if success:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
