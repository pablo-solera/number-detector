"""
Interfaz grafica de usuario con tkinter
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import time
from datetime import datetime

import config
from src.detector import RedNumberDetector
from src.exporter import ExcelExporter


class DetectorUI:
    def __init__(self, root):
        self.root = root
        self.root.title(config.UI_WINDOW_TITLE)
        self.root.geometry(config.UI_WINDOW_SIZE)
        self.root.resizable(True, True)

        # Variables
        self.input_folder = tk.StringVar(value=str(config.INPUT_DIR))
        self.output_folder = tk.StringVar(value=str(config.OUTPUT_DIR))
        self.s_min = tk.IntVar(value=config.RED_S_MIN)
        self.v_min = tk.IntVar(value=config.RED_V_MIN)
        self.max_workers = tk.IntVar(value=config.MAX_WORKERS or 4)
        self.debug_mode = tk.BooleanVar(value=config.DEBUG_MODE)

        self.is_processing = False
        self.image_count = 0

        # Configurar estilo
        self.setup_style()

        # Crear interfaz
        self.create_widgets()

        # Actualizar contador inicial
        self.update_image_count()

    def setup_style(self):
        """Configurar estilos de ttk"""
        style = ttk.Style()
        style.theme_use(config.UI_THEME)

        # Estilo para botones
        style.configure('Primary.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=10)

        style.configure('Success.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=10)

        # Estilo para labels
        style.configure('Title.TLabel',
                       font=('Segoe UI', 16, 'bold'),
                       foreground=config.UI_COLOR_PRIMARY)

        style.configure('Subtitle.TLabel',
                       font=('Segoe UI', 11, 'bold'))

        style.configure('Info.TLabel',
                       font=('Segoe UI', 9))

    def create_widgets(self):
        """Crear todos los widgets de la interfaz"""

        # Frame principal con padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        row = 0

        # ===== TITULO =====
        title = ttk.Label(main_frame, text="Detector de Numeros Rojos",
                         style='Title.TLabel')
        title.grid(row=row, column=0, columnspan=3, pady=(0, 20))
        row += 1

        # ===== SECCION: CARPETAS =====
        folder_frame = ttk.LabelFrame(main_frame, text="Carpetas", padding="10")
        folder_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        folder_frame.columnconfigure(1, weight=1)
        row += 1

        # Input folder
        ttk.Label(folder_frame, text="Carpeta de entrada:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(folder_frame, textvariable=self.input_folder, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(folder_frame, text="Examinar...", command=self.browse_input).grid(row=0, column=2)

        # Image count
        self.image_count_label = ttk.Label(folder_frame, text="Imagenes: 0", style='Info.TLabel')
        self.image_count_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))

        # Output folder
        ttk.Label(folder_frame, text="Carpeta de salida:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        ttk.Entry(folder_frame, textvariable=self.output_folder, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(10, 0))
        ttk.Button(folder_frame, text="Examinar...", command=self.browse_output).grid(row=2, column=2, pady=(10, 0))

        # ===== SECCION: CONFIGURACION =====
        config_frame = ttk.LabelFrame(main_frame, text="Configuracion de Deteccion", padding="10")
        config_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        row += 1

        # S_min
        ttk.Label(config_frame, text="Saturacion minima (S):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        s_scale = ttk.Scale(config_frame, from_=0, to=255, variable=self.s_min, orient=tk.HORIZONTAL)
        s_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.s_label = ttk.Label(config_frame, text=f"{self.s_min.get()}")
        self.s_label.grid(row=0, column=2)
        s_scale.configure(command=lambda v: self.s_label.config(text=f"{int(float(v))}"))

        # V_min
        ttk.Label(config_frame, text="Brillo minimo (V):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        v_scale = ttk.Scale(config_frame, from_=0, to=255, variable=self.v_min, orient=tk.HORIZONTAL)
        v_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(10, 0))
        self.v_label = ttk.Label(config_frame, text=f"{self.v_min.get()}")
        self.v_label.grid(row=1, column=2, pady=(10, 0))
        v_scale.configure(command=lambda v: self.v_label.config(text=f"{int(float(v))}"))

        # Nivel de permisividad
        self.level_label = ttk.Label(config_frame, text=self.get_level_text(), style='Info.TLabel')
        self.level_label.grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        s_scale.configure(command=lambda v: self.update_level_label())
        v_scale.configure(command=lambda v: self.update_level_label())

        # Presets
        preset_frame = ttk.Frame(config_frame)
        preset_frame.grid(row=3, column=0, columnspan=3, pady=(10, 0))

        ttk.Label(preset_frame, text="Presets:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(preset_frame, text="Muy Permisivo", command=lambda: self.load_preset(20, 20)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Permisivo", command=lambda: self.load_preset(50, 50)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Medio", command=lambda: self.load_preset(80, 80)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Restrictivo", command=lambda: self.load_preset(120, 120)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="Muy Restrictivo", command=lambda: self.load_preset(150, 150)).pack(side=tk.LEFT, padx=2)

        # ===== SECCION: OPCIONES AVANZADAS =====
        advanced_frame = ttk.LabelFrame(main_frame, text="Opciones Avanzadas", padding="10")
        advanced_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1

        # Max workers
        ttk.Label(advanced_frame, text="Procesos paralelos:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Spinbox(advanced_frame, from_=1, to=32, textvariable=self.max_workers, width=10).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(advanced_frame, text="(mas rapido con mas CPUs)", style='Info.TLabel').grid(row=0, column=2, sticky=tk.W, padx=(10, 0))

        # Debug mode
        ttk.Checkbutton(advanced_frame, text="Modo debug (guardar imagenes intermedias)",
                       variable=self.debug_mode).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(10, 0))

        # ===== SECCION: ACCIONES =====
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=row, column=0, columnspan=3, pady=(10, 0))
        row += 1

        self.process_button = ttk.Button(action_frame, text="PROCESAR IMAGENES",
                                        command=self.start_processing,
                                        style='Primary.TButton',
                                        width=30)
        self.process_button.pack(side=tk.LEFT, padx=5)

        self.cancel_button = ttk.Button(action_frame, text="Cancelar",
                                       command=self.cancel_processing,
                                       state=tk.DISABLED)
        self.cancel_button.pack(side=tk.LEFT, padx=5)

        # ===== SECCION: PROGRESO =====
        progress_frame = ttk.LabelFrame(main_frame, text="Progreso", padding="10")
        progress_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        progress_frame.columnconfigure(0, weight=1)
        row += 1

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        self.status_label = ttk.Label(progress_frame, text="Listo para procesar", style='Info.TLabel')
        self.status_label.grid(row=1, column=0, sticky=tk.W)

        # ===== SECCION: LOG =====
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(row, weight=1)

        # Text widget con scrollbar
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD,
                               yscrollcommand=log_scroll.set,
                               font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scroll.config(command=self.log_text.yview)

    def get_level_text(self):
        """Obtener texto descriptivo del nivel de permisividad"""
        avg = (self.s_min.get() + self.v_min.get()) / 2
        if avg <= 30:
            return "Nivel: MUY PERMISIVO (detecta casi cualquier rojizo)"
        elif avg <= 70:
            return "Nivel: PERMISIVO (mayoria de rojos)"
        elif avg <= 110:
            return "Nivel: MEDIO (balance)"
        elif avg <= 140:
            return "Nivel: RESTRICTIVO (solo rojos intensos)"
        else:
            return "Nivel: MUY RESTRICTIVO (solo rojos muy puros)"

    def update_level_label(self):
        """Actualizar etiqueta de nivel"""
        self.level_label.config(text=self.get_level_text())

    def load_preset(self, s, v):
        """Cargar un preset de valores"""
        self.s_min.set(s)
        self.v_min.set(v)
        self.s_label.config(text=str(s))
        self.v_label.config(text=str(v))
        self.update_level_label()
        self.log(f"Preset cargado: S={s}, V={v}")

    def browse_input(self):
        """Seleccionar carpeta de entrada"""
        folder = filedialog.askdirectory(initialdir=self.input_folder.get())
        if folder:
            self.input_folder.set(folder)
            self.update_image_count()

    def browse_output(self):
        """Seleccionar carpeta de salida"""
        folder = filedialog.askdirectory(initialdir=self.output_folder.get())
        if folder:
            self.output_folder.set(folder)

    def update_image_count(self):
        """Actualizar contador de imagenes"""
        input_dir = Path(self.input_folder.get())
        if input_dir.exists():
            images = []
            for ext in config.IMAGE_EXTENSIONS:
                images.extend(input_dir.glob(f"*{ext}"))
            self.image_count = len(images)
            self.image_count_label.config(text=f"Imagenes encontradas: {self.image_count}")
        else:
            self.image_count = 0
            self.image_count_label.config(text="Carpeta no existe")

    def log(self, message):
        """Agregar mensaje al log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_processing(self):
        """Iniciar procesamiento en un thread separado"""
        if self.is_processing:
            return

        # Validaciones
        input_dir = Path(self.input_folder.get())
        if not input_dir.exists():
            messagebox.showerror("Error", "La carpeta de entrada no existe")
            return

        if self.image_count == 0:
            messagebox.showwarning("Advertencia", "No hay imagenes para procesar")
            return

        # Actualizar UI
        self.is_processing = True
        self.process_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.progress_bar['value'] = 0
        self.log_text.delete(1.0, tk.END)

        # Iniciar procesamiento en thread
        thread = threading.Thread(target=self.process_images, daemon=True)
        thread.start()

    def cancel_processing(self):
        """Cancelar procesamiento (placeholder)"""
        self.log("Cancelacion solicitada...")
        # TODO: Implementar cancelacion real

    def process_images(self):
        """Procesar imagenes (ejecutado en thread separado)"""
        try:
            self.log("="*50)
            self.log("INICIANDO PROCESAMIENTO")
            self.log("="*50)

            # Obtener imagenes
            input_dir = Path(self.input_folder.get())
            output_dir = Path(self.output_folder.get())
            output_dir.mkdir(exist_ok=True)

            image_paths = []
            for ext in config.IMAGE_EXTENSIONS:
                image_paths.extend(input_dir.glob(f"*{ext}"))

            self.log(f"Imagenes encontradas: {len(image_paths)}")
            self.log(f"Configuracion: S_min={self.s_min.get()}, V_min={self.v_min.get()}")
            self.log(f"Procesos paralelos: {self.max_workers.get()}")
            self.log("")

            # Actualizar config temporal
            config.RED_S_MIN = self.s_min.get()
            config.RED_V_MIN = self.v_min.get()
            config.RED_LOWER_1 = [0, self.s_min.get(), self.v_min.get()]
            config.RED_LOWER_2 = [170, self.s_min.get(), self.v_min.get()]
            config.DEBUG_MODE = self.debug_mode.get()

            # Crear detector
            debug_dir = output_dir / "debug" if self.debug_mode.get() else None
            detector = RedNumberDetector(debug=self.debug_mode.get(), debug_dir=debug_dir)

            # Procesar
            start_time = time.time()
            results = detector.process_batch(image_paths, max_workers=self.max_workers.get())
            elapsed = time.time() - start_time

            # Preparar datos para Excel
            self.log("Preparando datos para Excel...")
            rows = []
            for image_path, (numbers, motors) in results.items():
                if not motors:
                    motors = [""]

                for number in numbers:
                    motor_str = ", ".join(motors)
                    rows.append([
                        image_path.name.split(".")[0],
                        number,
                        motor_str
                    ])

            # Exportar
            self.log("Exportando a Excel...")
            output_file = output_dir / config.OUTPUT_FILENAME
            exporter = ExcelExporter(output_file)
            exporter.export(rows)

            # Resumen
            self.log("")
            self.log("="*50)
            self.log("PROCESAMIENTO COMPLETADO")
            self.log("="*50)
            self.log(f"Tiempo total: {elapsed:.2f} segundos")
            self.log(f"Tiempo promedio: {elapsed/len(results):.2f}s por imagen")
            self.log(f"Filas generadas: {len(rows)}")
            self.log(f"Excel guardado en: {output_file}")
            self.log("="*50)

            self.progress_bar['value'] = 100
            self.status_label.config(text="Completado exitosamente")

            messagebox.showinfo("Exito", f"Procesamiento completado!\n\nArchivo: {output_file}")

        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            self.status_label.config(text="Error en el procesamiento")
            messagebox.showerror("Error", f"Error durante el procesamiento:\n{str(e)}")

        finally:
            self.is_processing = False
            self.process_button.config(state=tk.NORMAL)
            self.cancel_button.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = DetectorUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()