from pandas import DataFrame


class ExcelExporter:
    def __init__(self, output_path):
        self.output_path = output_path

    def export(self, rows):
        """
        Exporta los datos a Excel sin formato.
        El nombre del archivo solo aparece en la primera fila de cada grupo.

        rows: lista de tuplas/listas con formato:
        [
            ('16_26_1', '709', '1.5/B38A15P'),
            ('16_26_1', '1051', '1.5/B38A15P'),
            ...
        ]
        """
        if not rows:
            print("\nNo hay datos para exportar")
            return

        # Crear DataFrame
        df = DataFrame(
            rows,
            columns=["Archivo", "Numero", "Motor"]
        )

        # Agrupar por archivo: mostrar nombre solo en primera fila
        df_grouped = df.copy()

        # Identificar donde cambia el archivo
        df_grouped['archivo_changed'] = df_grouped['Archivo'] != df_grouped['Archivo'].shift(1)

        # Donde NO haya cambio de archivo, dejar la celda vacia
        df_grouped.loc[~df_grouped['archivo_changed'], 'Archivo'] = ''

        # Eliminar columna auxiliar
        df_grouped = df_grouped.drop('archivo_changed', axis=1)

        # Exportar a Excel SIN formato
        df_grouped.to_excel(self.output_path, index=False, sheet_name='Numeros Rojos')

        print(f"\nResultados exportados a: {self.output_path}")
        print(f"  Total de registros: {len(rows)}")
        print(f"  Archivos procesados: {df['Archivo'].nunique()}")
