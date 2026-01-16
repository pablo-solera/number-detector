# Detector de Números Rojos en Imágenes

Script en Python que detecta números en color rojo dentro de imágenes y los exporta a un archivo Excel.

## Instalación

### 1. Clonar o descargar el proyecto

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar Tesseract OCR

- Descarga desde: https://github.com/UB-Mannheim/tesseract/wiki
- Instala y ajusta la ruta en `config.py` si es necesario

## Uso

1. Coloca tus imágenes (.jpg, .png, etc.) en la carpeta `input/`

2. Ejecuta el script:

```bash
python main.py
```

3. El archivo Excel se generará en `output/numeros_rojos.xlsx`

## Configuración

Puedes ajustar parámetros en `config.py`:

- Rangos de color rojo (HSV)
- Tamaño mínimo de contornos
- Configuración de OCR
- Rutas de directorios

## Generar .exe

pyinstaller --onefile --windowed --noconsole --name "DetectorNumeros" --icon=img/icon.ico main.py

## Formato de Salida

El Excel generado tendrá el siguiente formato:

| Archivo | Número | Motor       |
|---------|--------|-------------|
| 16_26_1 | 709    | 1.5/B38A15P |
| 16_26_1 | 1051   | 1.5/B38A15P |
| 16_26_1 | 10635  | 1.5/B38A15P |
