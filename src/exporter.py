import pandas as pd


class ExcelExporter:
    def __init__(self, output_path):
        self.output_path = output_path

    def export(self, rows):
        if not rows:
            return

        df = pd.DataFrame(
            rows,
            columns=["Archivo", "Número", "Motor"]
        )
        df.to_excel(self.output_path, index=False)