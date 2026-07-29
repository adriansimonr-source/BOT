from core.process_manager import ProcessManager
from core.managers.screen_capture_manager import ScreenCaptureManager


process_manager = ProcessManager()


if process_manager.find_process(
    "KathanaGame.exe"
):

    print(
        "Proceso encontrado"
    )


    print(
        process_manager.get_window_position()
    )


    capture_manager = ScreenCaptureManager(
        process_manager.window_manager
    )


    result = capture_manager.save_capture(
        "game_capture.png"
    )


    if result:

        print(
            "Captura guardada"
        )

else:

    print(
        "Juego no encontrado"
    )