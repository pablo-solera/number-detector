from __future__ import annotations

from pathlib import Path

from pandas import DataFrame, ExcelWriter, to_numeric


class ExcelExporter:
    def __init__(self, output_path: str | None = None):
        self.output_path = output_path

    def export(self, rows: list[list[object]], output_path: str | Path | None = None) -> Path:
        if output_path is None and self.output_path is None:
            raise ValueError("output_path is required")
        destination = Path(output_path or self.output_path)

        if not rows:
            return destination

        df = DataFrame(rows, columns=["Archivo", "Numero", "Motor", "Free text"])
        df["Numero"] = to_numeric(df["Numero"], errors="coerce")

        df_grouped = df.copy()
        df_grouped["archivo_changed"] = df_grouped["Archivo"] != df_grouped["Archivo"].shift(1)
        df_grouped.loc[~df_grouped["archivo_changed"], "Archivo"] = ""
        df_grouped = df_grouped.drop("archivo_changed", axis=1)

        with ExcelWriter(destination, engine="xlsxwriter") as writer:
            df_grouped.to_excel(writer, index=False, sheet_name="Numeros Rojos")
            workbook = writer.book
            worksheet = writer.sheets["Numeros Rojos"]
            number_format = workbook.add_format({"num_format": "0"})
            worksheet.set_column("B:B", 15, number_format)

        return destination
