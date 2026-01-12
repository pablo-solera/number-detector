import pandas as pd
from pathlib import Path
import config


class ExcelExporter:
    @staticmethod
    def export_to_excel(data, output_path=None):
        if not data:
            print("\n⚠ No hay datos para exportar")
            return False
        
        if output_path is None:
            output_path = config.OUTPUT_DIR / config.OUTPUT_FILENAME
        
        df = pd.DataFrame(data)
        df.to_excel(output_path, index=False, sheet_name='Números Rojos')
        
        print(f"\n✓ Resultados exportados a: {output_path}")
        print(f"  Total de números encontrados: {len(data)}")
        
        return True
