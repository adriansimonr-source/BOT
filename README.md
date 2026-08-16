# SB Automation Suite

Suite no intrusiva de automatización por visión, OCR e input dirigido a una ventana de juego. Kathana en Windows 10 es el entorno de referencia actual. Captura/CV y automatización usan relojes separados; los automatismos, umbrales y tiempos auxiliares se pueden editar mientras el bot está activo, las habilidades `1..9` y `F1..F9` quedan bloqueadas durante la sesión, y el cierre espera de forma verificable a captura y OCR.

La GUI ofrece ayuda contextual en sus controles y marca F1–F9 como habilidades prioritarias para buffs/escudos. Esa prioridad solo arbitra acciones ya vencidas: no adelanta los intervalos configurados ni bloquea permanentemente las teclas `1..9`.

Los recursos visuales están aislados del resto del combate: F8/AutoPot1 y F10/AutoHeal consultan HP, F9/AutoMP consulta MP, y ninguna otra acción depende de esas lecturas. Un HP enemigo ilegible no se interpreta como objetivo ausente; solo se usa para clasificar enemigos frente a items y aplicar la lista de ignorados.

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
