import mss
import mss.tools


class ScreenCaptureManager:


    def __init__(
        self,
        window_manager
    ):

        self.window_manager = window_manager



    # ==================================================
    # Capturar ventana del juego
    # ==================================================

    def capture(self):

        window = (
            self.window_manager
            .get_position()
        )


        if window is None:

            return None



        monitor = {

            "left": window["x"],

            "top": window["y"],

            "width": window["width"],

            "height": window["height"]

        }


        with mss.mss() as sct:


            screenshot = sct.grab(
                monitor
            )


            return screenshot



    # ==================================================
    # Guardar captura (debug)
    # ==================================================

    def save_capture(
        self,
        filename="capture.png"
    ):

        screenshot = self.capture()


        if screenshot is None:

            return False



        with mss.mss() as sct:

            mss.tools.to_png(
                screenshot.rgb,
                screenshot.size,
                output=filename
            )


        return True