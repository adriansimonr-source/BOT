from core.process_manager import ProcessManager
from core.managers.windows_graphics_capture import WindowsGraphicsCaptureManager
from core.managers.direct3d_device import Direct3DDeviceManager
from core.managers.direct3d_converter import Direct3DConverter

import winrt.windows.graphics.capture.interop as wgc_interop



pm = ProcessManager()


if pm.find_process(
    "KathanaGame.exe"
):

    hwnd = pm.get_window_handle()


    print(
        "HWND:",
        hwnd
    )


    item = wgc_interop.create_for_window(
        hwnd
    )


    d3d = Direct3DDeviceManager()

    d3d.create_device()


    converter = Direct3DConverter()

    converter.create_winrt_device(
        d3d.get_device()
    )


    capture = WindowsGraphicsCaptureManager(
        hwnd
    )


    capture.initialize(
        item,
        converter.get_device()
    )


else:

    print(
        "Juego no encontrado"
    )