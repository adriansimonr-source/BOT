# SB Automation Suite

Suite no intrusiva de automatización por visión, OCR e input dirigido a una ventana de juego. Kathana en Windows 10 es el entorno de referencia actual. Captura/CV y automatización usan relojes separados; los checks, umbrales y tiempos se pueden editar mientras el bot está activo, y el cierre espera de forma verificable a captura y OCR.

La arquitectura, el contrato de combate y navegación, las dependencias, la instalación, la compatibilidad y el estado del proyecto están consolidados en [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md).

## Inicio rápido

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Tesseract debe instalarse por separado y estar disponible en `PATH`. Para validar el entorno:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Estado de plataformas: Windows 10 operativo desde código; Windows 11 pendiente de validación; Ubuntu no dispone todavía de backends de captura e input.
