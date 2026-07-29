import bettercam
import cv2


class ScreenCaptureManager:


    def __init__(
        self,
        window_manager
    ):

        self.window_manager = window_manager

        # Crear capturador
        self.camera = bettercam.create()



    # =====================================
    # Captura monitor
    # =====================================

    def capture(self):

        frame = self.camera.grab()


        print(
            "BETTERCAM FRAME:",
            None if frame is None else frame.shape
        )


        return frame



    # =====================================
    # Captura ventana
    # =====================================

    def capture_window(self):

        frame = self.capture()


        if frame is None:

            print(
                "No hay frame"
            )

            return None



        position = (
            self.window_manager.get_position()
        )


        print(
            "WINDOW POSITION:",
            position
        )



        if position is None:

            return frame



        x = position["x"]

        y = position["y"]

        width = position["width"]

        height = position["height"]



        crop = frame[
            y:y+height,
            x:x+width
        ]


        print(
            "CROP:",
            crop.shape
        )


        return crop



    # =====================================
    # Guardar captura
    # =====================================

    def save_capture(
        self,
        filename="game_capture.png"
    ):


        frame = self.capture_window()


        if frame is None:

            return False



        if frame.size == 0:

            print(
                "Imagen vacía"
            )

            return False



        result = cv2.imwrite(
            filename,
            frame
        )


        print(
            "WRITE:",
            result
        )


        return result