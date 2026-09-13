# SB Automation Suite

Suite no intrusiva de automatización por visión, OCR e input dirigido a una ventana de juego. Kathana en Windows 10 es el entorno de referencia actual. Captura/CV y automatización usan relojes separados; los automatismos, umbrales y tiempos auxiliares se pueden editar mientras el bot está activo, las habilidades `1..9` y `F1..F7` quedan bloqueadas durante la sesión, y el cierre espera de forma verificable a captura y OCR.

La GUI abre a 640×320 y es redimensionable. Los layouts fijan un mínimo útil aproximado de 522–531×319 en Windows 11, evitando solapes sin depender de la resolución física. `PERSONAJE` muestra únicamente HP y MP; la posición, el origen, el radio y sus botones ya no ocupan espacio, aunque su lógica interna se conserva. `TARGET` muestra el nombre y la barra HP sin el campo `LVL`. Se ha validado el comportamiento nativo con escalado de pantalla del 100% al 200%.

A la derecha de `TARGET`, `PERFIL` permite seleccionar uno existente o escribir uno nuevo. El botón de disquete crea o actualiza ese perfil con los checks, umbrales y tiempos actuales de automatismos, consumibles, habilidades e ignorados; la `×` elimina el perfil seleccionado tras confirmarlo. Al elegir `Sin perfil`, todos los checks se desactivan y los valores vuelven a sus ajustes iniciales.

La GUI ofrece ayuda contextual en sus controles y marca F1–F7 como habilidades prioritarias para buffs/escudos. Esa prioridad solo arbitra acciones ya vencidas: no adelanta los intervalos configurados. La rotación no conserva colas ni buffers: en una colisión intenta una sola skill, prioriza `F1..F7` y descarta las demás ocurrencias hasta su siguiente periodo. F8 y F9 quedan reservadas para AutoPot1 y AutoMP. Las skills temporizadas continúan si la visión se retrasa mientras el proceso del juego siga conectado.

Los recursos visuales están aislados del resto del combate: F8/AutoPot1 y F10/AutoHeal consultan HP, mientras F9/AutoMP consulta MP. AutoTarget dispone de un tiempo editable, por defecto 10.000 ms, para cambiar una selección sin progreso; cada nuevo mínimo válido de vida reinicia el plazo. Un HP enemigo ilegible no se interpreta como cero ni como objetivo ausente, pero tampoco permite que una selección atascada bloquee el bot indefinidamente.

Tras perder el objetivo de un combate, AutoLoot reserva la primera recogida: espera cinco segundos, pausa temporalmente AutoTarget y el retorno, envía `F` y después permite continuar con el siguiente objetivo.

La arquitectura, el contrato de combate y navegación, las dependencias, la instalación, la compatibilidad y el estado del proyecto están consolidados en [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md).

## Estado de la build para Windows

La build actual es `Windows_11_lite_v1.0_x64.msix`, para Windows 11 x64 build 22000 o posterior. Está firmada con el certificado de desarrollo del proyecto y se entrega junto a su parte pública y las instrucciones de instalación en `release/`. El 13 de septiembre de 2026 superó los 306 tests, el smoke test del ejecutable, la verificación de firma y contenido y una instalación temporal real con estado `Ok`.

En Windows 11 la aplicación exige que el sistema conceda y aplique la captura WGC sin borde. Si no puede hacerlo, la captura no arranca y muestra un error en vez de continuar con el marco amarillo. Para declarar las capacidades requeridas, la distribución de Windows 11 debe instalarse como un MSIX firmado; el ZIP portable no proporciona identidad de paquete y no garantiza ese permiso. En el primer inicio Windows puede pedir confirmación y hay hasta 60 segundos para responder. Otra aplicación que capture simultáneamente la misma ventana aún puede obligar al sistema a mostrar el borde. Windows 10 conserva la compatibilidad anterior.

La configuración, perfiles y BBDD de una build se guardan en `%LOCALAPPDATA%\SB Automation Suite\data`, por lo que una actualización no los sobrescribe. La vuelta al origen sigue pendiente de mejora.

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

Para reproducir la distribución de Windows 11 x64 se necesita Windows 11 SDK 10.0.22000 o posterior y un certificado de firma de código con clave privada. El comando debe recibir el thumbprint del certificado disponible en cada equipo de desarrollo. Antes de instalar una MSIX autofirmada, su certificado público debe importarse con permisos de administrador en `Cert:\LocalMachine\TrustedPeople`. Los datos del entorno local actual se conservan en `PROJECT_CONTEXT.md`; ninguna clave privada forma parte del repositorio.

```powershell
.\scripts\build_windows.ps1 -Version 1.0 -ArtifactName Windows_11_lite_v1.0 -SkipArchive
.\scripts\package_windows_msix.ps1 `
    -SourceDirectory .\dist\Windows_11_lite_v1.0 `
    -ArtifactName Windows_11_lite_v1.0 `
    -Version 1.0 `
    -CertificateThumbprint <THUMBPRINT>
```

El primer script valida dependencias y tests, genera el `onedir`, comprueba `python314.dll`, recursos, Tesseract y el arranque del ejecutable. El segundo crea `release/Windows_11_lite_v1.0_x64.msix`, incorpora las capacidades de captura, firma el paquete, verifica la firma y vuelve a inspeccionar su contenido. También exporta el certificado público y las instrucciones de instalación; no distribuye la clave privada. La suite actual tiene 306 tests en verde; Ubuntu todavía no dispone de backends de captura e input.
