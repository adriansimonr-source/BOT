import cv2


class WindowsGraphicsCaptureManager:


    def __init__(
        self,
        hwnd
    ):

        self.hwnd = hwnd

        self.initialized = False



    # =====================================
    # Inicialización
    # =====================================

    def initialize(self):

        print(
            "Inicializando Windows Graphics Capture"
        )

        print(
            "HWND:",
            self.hwnd
        )


        if self.hwnd is None:

            print(
                "HWND no válido"
            )

            return False



        # Aquí irá:
        #
        # 1. Crear GraphicsCaptureItem
        # 2. Crear Direct3D11 Device
        # 3. Crear FramePool
        # 4. Crear Session


        self.initialized = True


        return True



    # =====================================
    # Capturar frame
    # =====================================

    def capture(self):


        if not self.initialized:

            if not self.initialize():

                return None



        # Aquí devolveremos:
        #
        # numpy.ndarray
        #
        # ejemplo:
        #
        # frame.shape
        # (1080,1920,4)


        return None



    # =====================================
    # Guardar captura
    # =====================================

    def save_capture(
        self,
        filename="wgc_capture.png"
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


        print(
            "Captura guardada:",
            filename
        )


        return True



    # =====================================
    # Estado
    # =====================================

    def is_initialized(self):

        return self.initialized