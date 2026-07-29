from core.process_manager import ProcessManager
from core.managers.windows_graphics_capture import WindowsGraphicsCaptureManager

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



    item = (
        wgc_interop
        .create_for_window(
            hwnd
        )
    )


    print(
        "ITEM:",
        item
    )



    capture = WindowsGraphicsCaptureManager(
        hwnd
    )


    print(
        "Item creado correctamente"
    )


else:

    print(
        "Juego no encontrado"
    )