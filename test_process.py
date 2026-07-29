from core.process_manager import ProcessManager
from core.managers.windows_graphics_capture import WindowsGraphicsCaptureManager



process_manager = ProcessManager()



if process_manager.find_process(
    "KathanaGame.exe"
):

    print(
        "Proceso encontrado"
    )


    hwnd = (
        process_manager
        .get_window_handle()
    )


    print(
        "HWND:",
        hwnd
    )



    capture = (
        WindowsGraphicsCaptureManager(
            hwnd
        )
    )


    capture.save_capture(
        "wgc_test.png"
    )


else:

    print(
        "Juego no encontrado"
    )