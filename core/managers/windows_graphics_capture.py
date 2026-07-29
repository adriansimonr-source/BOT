import winrt.windows.graphics.capture as capture


class WindowsGraphicsCaptureManager:


    def __init__(
        self,
        hwnd
    ):

        self.hwnd = hwnd

        self.item = None

        self.frame_pool = None

        self.session = None



    # =====================================
    # Inicializar
    # =====================================

    def initialize(
        self,
        item,
        device
    ):

        self.item = item



        print(
            "Creando FramePool real"
        )


        self.frame_pool = (
            capture.Direct3D11CaptureFramePool.create_free_threaded(
                device,
                capture.DirectXPixelFormat.B8G8R8A8UIntNormalized,
                2,
                item.size
            )
        )


        self.session = (
            self.frame_pool.create_capture_session(
                item
            )
        )


        self.session.start_capture()


        print(
            "Captura iniciada"
        )


        return True