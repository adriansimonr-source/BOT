# Build, dependencias y compatibilidad

Documento de referencia para ejecutar y distribuir SB Automation Suite. El estado descrito corresponde a la auditoría del 11 de agosto de 2026.

## Entorno validado

- Sistema de desarrollo: Windows 10 20H2 x64.
- Python validado: 3.14.6.
- Entrada: mensajes Win32 dirigidos al `HWND` mediante `SendMessageTimeout`.
- Captura: Windows Graphics Capture (WGC) + D3D11.
- OCR: Tesseract, invocado mediante `pytesseract`.

La ejecución desde código y la suite automatizada están validadas en ese entorno. Todavía no existe un artefacto instalable reproducible ni una validación completa en Windows 11 o Linux.

## Dependencias

`requirements.txt` es la fuente canónica. La auditoría redujo sus 14 entradas a 9 dependencias directas:

| Dependencia | Uso |
| --- | --- |
| `PySide6_Essentials` | GUI Qt sin los módulos Addons que el proyecto no importa |
| `numpy` | Procesamiento de frames y máscaras |
| `opencv-python-headless` | Visión sin duplicar una segunda GUI |
| `psutil` | Detección y validación de procesos |
| `pytesseract` | Puente Python hacia Tesseract |
| `comtypes`, `pywin32` | COM, ventanas e input en Windows |
| `winrt-runtime`, `winrt-Windows.Graphics.Capture` | WGC y solicitud de captura sin borde |

Las dependencias exclusivas de Windows llevan marcador `sys_platform == "win32"`. Se retiraron el metapaquete `PySide6`, Addons, `shiboken6` explícito y namespaces WinRT no importados. Una instalación limpia debe contener una sola distribución de OpenCV: `opencv-python-headless`.

## Instalación desde cero

Ejecutar desde la raíz del repositorio:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

Tesseract no forma parte del wheel de `pytesseract`. Debe instalarse por separado y su ejecutable debe quedar en `PATH`:

```powershell
tesseract --version
```

Arranque y validación:

```powershell
.\.venv\Scripts\python.exe main.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

La aplicación usa rutas relativas (`data/config.json`, `data/games.json`, `data/entities/`, logo y plantillas). Hasta incorporar un resolvedor de recursos, debe iniciarse desde la raíz del proyecto.

## Matriz de plataforma

| Plataforma | Estado real |
| --- | --- |
| Windows 10 20H2 x64 | Entorno de referencia validado desde código. WGC conserva el marco amarillo del sistema. |
| Windows 10 1903+ | Diseño compatible con WGC, pero cada build objetivo debe probarse. |
| Windows 11 x64 | Ruta prevista. El código solicita captura sin borde cuando la API lo permite; falta validar permisos, identidad de paquete y artefacto final. |
| Ubuntu 24.04 X11/Wayland | No compatible: faltan backends de captura, ventanas e input y aún existen imports Win32 de arranque. |
| macOS | Fuera del plan actual. |

El marco de WGC no se incluye en el frame entregado a visión ni en el OCR. Su coste en el compositor no se ha medido. En sistemas compatibles, la aplicación intenta desactivarlo; una API ausente o un permiso denegado conserva el borde sin interrumpir la captura.

Las builds deben generarse de forma nativa en cada sistema. Una build de Windows no sustituye a una build Linux y viceversa.

## Estado del empaquetado

No hay `spec` de PyInstaller, dependencia de build fijada ni instalador probado. Por tanto, no debe afirmarse que existe una build reproducible. Para cerrar esa fase hay que:

1. Fijar la herramienta de empaquetado en requisitos de desarrollo separados.
2. Crear un `spec` Windows x64 y declarar logo, `data/templates.json`, los tres anchors, configuración, perfiles y BBDD iniciales.
3. Resolver recursos de solo lectura dentro del bundle y mover configuración/BBDD mutable a un directorio de usuario.
4. Decidir si Tesseract y sus datos se incluyen o se mantienen como prerrequisito externo.
5. Validar arranque, captura, OCR, input, persistencia y cierre en una máquina limpia de Windows 10 y otra de Windows 11.
6. Validar el permiso/capacidad de captura sin borde en el formato de paquete elegido.

Ubuntu requerirá primero adaptadores independientes para X11 y Wayland; no debe añadirse un empaquetado Linux sobre los imports Win32 actuales.

## Checklist de entrega

- Instalación limpia desde `requirements.txt` y `pip check` sin errores.
- Tesseract localizable y OCR numérico/textual operativo.
- Suite completa en verde.
- Arranque desde un directorio sin el entorno de desarrollo.
- Selección de juego, captura del `HWND` correcto e input en segundo plano.
- Inicio/parada repetidos sin crecimiento sostenido de memoria ni recursos D3D abiertos.
- Escritura de configuración y BBDD fuera de una ubicación de solo lectura.
- Smoke test específico por versión de Windows soportada.
