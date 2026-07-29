import cv2
import numpy as np


class WindowsGraphicsCaptureManager:


    def __init__(
        self,
        hwnd
    ):

        self.hwnd = hwnd



    # =====================================
    # Capturar ventana
    # =====================================

    def capture(self):

        """
        Aquí irá Windows.Graphics.Capture
        """

        print(
            "Captura WGC HWND:",
            self.hwnd
        )


        return None



    # =====================================
    # Guardar captura
    # =====================================

    def save_capture(
        self,
        filename="game_capture.png"
    ):


        frame = self.capture()


        if frame is None:

            print(
                "No se pudo capturar ventana"
            )

            return False



        cv2.imwrite(
            filename,
            frame
        )


        return True