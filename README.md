# Detector de Números Rojos en Imágenes

Script en Python que detecta números en color rojo dentro de imágenes y los exporta a un archivo Excel.

## Estructura del Proyecto

```
red-number-detector/
├── README.md
├── requirements.txt
├── .gitignore
├── config.py
├── main.py
├── input/              # Coloca aquí tus imágenes
├── output/             # Aquí se generará el Excel
└── src/
    ├── __init__.py
    ├── detector.py
    └── exporter.py
```

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

**Windows:**
- Descarga desde: https://github.com/UB-Mannheim/tesseract/wiki
- Instala y ajusta la ruta en `config.py` si es necesario

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**Mac:**
```bash
brew install tesseract
```

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

## Formato de Salida

El Excel generado tendrá el siguiente formato:

| Archivo  | Número |
|----------|--------|
| 16_26_1  | 709    |
| 16_26_1  | 1051   |
| 16_26_1  | 10635  |

## Solución de Problemas

**No detecta números:**
- Ajusta los rangos de color rojo en `config.py`
- Verifica que Tesseract esté correctamente instalado

**Error con Tesseract:**
- Windows: Configura `TESSERACT_CMD` en `config.py`
- Linux/Mac: Verifica que tesseract esté en el PATH

## Licencia

MIT
