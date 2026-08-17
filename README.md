# SB Automation Suite v1.1.1

Suite no intrusiva de automatización por visión, OCR e input dirigido a una ventana de juego. Kathana en Windows 10 es el entorno de referencia actual. Captura/CV y automatización usan relojes separados; los automatismos, umbrales y tiempos auxiliares se pueden editar mientras el bot está activo, las habilidades `1..9` y `F1..F7` quedan bloqueadas durante la sesión, y el cierre espera de forma verificable a captura y OCR.

La GUI de 480×320 muestra el panel operativo sin pestañas `BOT/LOG`; HP y MP comparten una fila, y `TARGET`, `LVL` y la barra de vida enemiga quedan juntos en la siguiente. El control de inicio/parada está a la derecha de GAME. RADIO ofrece `FIJO`, `SIN LÍMITE`, `10`, `20`, `30` y `40`, con `40` como valor inicial.

La GUI ofrece ayuda contextual en sus controles y marca F1–F7 como habilidades prioritarias para buffs/escudos. Esa prioridad solo arbitra acciones ya vencidas: no adelanta los intervalos configurados. La rotación no conserva colas ni buffers: en una colisión intenta una sola skill, prioriza `F1..F7` y descarta las demás ocurrencias hasta su siguiente periodo. F8 y F9 quedan reservadas para AutoPot1 y AutoMP. Las skills temporizadas continúan si la visión se retrasa mientras el proceso del juego siga conectado.

Los recursos visuales están aislados del resto del combate: F8/AutoPot1 y F10/AutoHeal consultan HP, mientras F9/AutoMP consulta MP. AutoTarget dispone de un tiempo editable, por defecto 10.000 ms, para cambiar una selección sin progreso; cada nuevo mínimo válido de vida reinicia el plazo. Un HP enemigo ilegible no se interpreta como cero ni como objetivo ausente, pero tampoco permite que una selección atascada bloquee el bot indefinidamente.

Tras perder el objetivo de un combate, AutoLoot reserva la primera recogida: espera cinco segundos, pausa temporalmente AutoTarget y el retorno, envía `F` y después permite continuar con el siguiente objetivo.

La arquitectura, el contrato de combate y navegación, las dependencias, la instalación, la compatibilidad y el estado del proyecto están consolidados en [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md).

## Build portable para Windows

La build x64 está en `release/SB_Automation_Suite_v1.1.1_Windows_x64.zip` (SHA-256 `31A838B0085DA557363F3810E37C62FB1D108F9143B49CFA07D7741EC09915AB`). Hay que extraer la carpeta completa antes de ejecutar `SB_Automation_Suite.exe`; no se debe abrir desde dentro del ZIP ni separar el ejecutable de `_internal`. `LEEME_PRIMERO.txt` conserva estas instrucciones junto al ejecutable. No requiere instalar Python ni Tesseract.

La configuración, perfiles y BBDD de la build se conservan en `%LOCALAPPDATA%\SB Automation Suite\data`, por lo que sustituir la carpeta de la aplicación no los sobrescribe. La v1.1.1 está validada por 292 tests, un smoke desde `dist` y otro desde una extracción limpia del ZIP. La prueba real del bot en Windows 10 corresponde a la línea v1.1; la vuelta al origen sigue pendiente de mejora. Todavía no es un instalador firmado ni se ha certificado en un Windows 11 limpio.

## Inicio rápido

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Al ejecutar desde código, Tesseract debe instalarse por separado y estar disponible en `PATH`. Para validar el entorno:

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Para reconstruir la distribución en Windows x64:

```powershell
.\scripts\build_windows.ps1 -Version 1.1.1
```

El script usa `requirements-build.txt`, crea un entorno limpio, ejecuta las pruebas, exige la DLL de Python y valida tanto la carpeta generada como una extracción nueva del ZIP antes de publicarlo. Estado de plataformas: Windows 10 operativo desde código y con build portable; Windows 11 pendiente de validación; Ubuntu no dispone todavía de backends de captura e input.
