from core.process_manager import ProcessManager
from core.managers.wgc_com_capture import WGCComCapture



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
        "HWND encontrado:",
        hwnd
    )



    wgc = WGCComCapture(
        hwnd
    )



    result = (
        wgc.initialize()
    )



    print(
        "RESULTADO:",
        result
    )



else:

    print(
        "Juego no encontrado"
    )