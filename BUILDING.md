# Builds y compatibilidad

## Estado actual

| Sistema | Captura | Entrada en segundo plano | Estado de build |
| --- | --- | --- | --- |
| Windows 10 1903+ | WGC por HWND, con marco del sistema | Win32 `SendMessageTimeout` | Compatible |
| Windows 11 | WGC por HWND; sin marco si el usuario lo autoriza | Win32 `SendMessageTimeout` | Compatible; MSIX necesario para declarar la capacidad |
| Ubuntu 24.04 X11 | Backend pendiente | Backend XTest pendiente | No publicable todavía |
| Ubuntu 24.04 Wayland | Portal ScreenCast/PipeWire pendiente | Portal RemoteDesktop/libei pendiente | No publicable todavía |

El marco de WGC no forma parte de los frames procesados y no afecta al OCR ni al consumo. `IsBorderRequired` apareció en la build 20348; Windows 10 cliente llega a la rama 19045, por lo que allí el marco es obligatorio si se conserva WGC.

En Windows compatible, el programa solicita `GraphicsCaptureAccessKind.Borderless`. Si Windows niega el permiso, falta identidad de paquete o la interfaz no existe, continúa capturando con marco.

El paquete MSIX de Windows 11 tendrá que declarar:

```xml
<uap11:Capability Name="graphicsCaptureWithoutBorder"/>
```

## Estrategia de distribución

Se mantendrá un núcleo común para GUI, automatización, OCR y BBDD, con adaptadores separados para captura, ventanas e input:

- `WindowsCaptureBackend`: WGC/D3D11.
- `WindowsInputBackend`: mensajes Win32 a un HWND.
- `X11CaptureBackend`: XComposite/SHM.
- `X11InputBackend`: XTest.
- `WaylandCaptureBackend`: XDG ScreenCast Portal y PipeWire.
- `WaylandInputBackend`: XDG RemoteDesktop Portal/libei con autorización visible.

Los artefactos deben construirse de forma nativa en cada sistema; PyInstaller no genera una build Linux desde Windows ni una build Windows desde Linux.

1. Crear primero una build Windows x64 `onedir` para Windows 10/11.
2. Corregir las rutas de recursos y mover configuración/BBDD mutable a `AppData` antes de instalar en `Program Files` o generar MSIX.
3. Envolver la build Windows 11 en MSIX para habilitar la capacidad sin marco.
4. Implementar y validar X11 antes de generar la build Ubuntu.
5. Añadir Wayland como backend separado, porque el sistema exige selección y autorización del usuario.

## Bloqueos antes de publicar

- Las rutas de `data/` todavía dependen del directorio de ejecución.
- Tesseract y sus datos de idioma deben instalarse o incluirse en el paquete.
- Ubuntu aún importa módulos Win32 durante el arranque y no tiene backend real.
- Las builds finales deben probarse en Windows 10, Windows 11, Ubuntu X11 y Ubuntu Wayland.

Referencias: [captura sin borde](https://learn.microsoft.com/en-us/uwp/api/windows.graphics.capture.graphicscapturesession.isborderrequired), [capacidades de paquete](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/app-capability-declarations), [ScreenCast Portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.ScreenCast.html), [RemoteDesktop Portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.RemoteDesktop.html) y [builds por plataforma con PyInstaller](https://pyinstaller.org/en/stable/usage.html#supporting-multiple-operating-systems).
