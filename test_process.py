from core.process_manager import ProcessManager

from core.managers.direct3d_device import (
    Direct3DDeviceManager
)

from core.managers.direct3d_converter import (
    Direct3DConverter
)

import winrt.windows.graphics.capture as capture
import winrt.windows.graphics.directx as directx
import winrt.windows.graphics.capture.interop as wgc_interop

from winrt.windows.foundation import Size



pm = ProcessManager()



if not pm.find_process(
    "KathanaGame.exe"
):

    print(
        "Juego no encontrado"
    )

    exit()



hwnd = pm.get_window_handle()



print(
    "HWND:",
    hwnd
)



# =====================================
# GraphicsCaptureItem
# =====================================

item = (
    wgc_interop
    .create_for_window(
        hwnd
    )
)



print(
    "ITEM OK"
)



# =====================================
# D3D11
# =====================================

d3d = Direct3DDeviceManager()


if not d3d.create_device():

    exit()



# =====================================
# Convertir a WinRT
# =====================================

converter = Direct3DConverter()


if not converter.create_winrt_device(
    d3d.get_device()
):

    exit()



device = converter.get_device()



print(
    "DEVICE WINRT:",
    device
)


print(
    "TIPO DEVICE:",
    type(device)
)



# =====================================
# Tamaño
# =====================================

position = (
    pm.get_window_position()
)



size = Size(
    position["width"],
    position["height"]
)



print(
    "SIZE:",
    size.width,
    size.height
)



# =====================================
# Crear FramePool
# =====================================

print(
    "CREANDO FRAMEPOOL"
)



pool = (
    capture
    .Direct3D11CaptureFramePool
    .create_free_threaded(
        device,

        directx
        .DirectXPixelFormat
        .B8_G8_R8_A8_UINT_NORMALIZED,

        2,

        size
    )
)



print(
    "FRAMEPOOL CREADO:"
)

print(
    pool
)