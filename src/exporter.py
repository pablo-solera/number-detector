from pandas import DataFrame, to_numeric
from pandas import ExcelWriter
from xlsxwriter import Workbook


class ExcelExporter:
    def __init__(self, output_path):
        self.output_path = output_path

    def export(self, rows):
        if not rows:
            print("\nNo hay datos para exportar")
            return

        df = DataFrame(
            rows,
            columns=["Archivo", "Numero", "Motor"]
        )

        df["Numero"] = to_numeric(df["Numero"], errors="coerce")

        df_grouped = df.copy()
        df_grouped["archivo_changed"] = (
            df_grouped["Archivo"] != df_grouped["Archivo"].shift(1)
        )
        df_grouped.loc[~df_grouped["archivo_changed"], "Archivo"] = ""
        df_grouped = df_grouped.drop("archivo_changed", axis=1)

        with ExcelWriter(self.output_path, engine="xlsxwriter") as writer:
            df_grouped.to_excel(
                writer,
                index=False,
                sheet_name="Numeros Rojos"
            )

            workbook = writer.book
            worksheet = writer.sheets["Numeros Rojos"]

            # 🔹 Formato numérico explícito
            number_format = workbook.add_format({"num_format": "0"})
            worksheet.set_column("B:B", 15, number_format)

        print(f"\nResultados exportados a: {self.output_path}")
        print(f"  Total de registros: {len(rows)}")
        print(f"  Archivos procesados: {df['Archivo'].nunique()}")
