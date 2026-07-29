import winrt.windows.graphics.capture as capture
import winrt.windows.graphics.directx as directx
import winrt.windows.foundation as foundation



class WindowsGraphicsCaptureManager:


    def __init__(
        self,
        hwnd
    ):

        self.hwnd = hwnd

        self.item = None

        self.device = None

        self.frame_pool = None

        self.session = None



    # =====================================
    # Inicializar captura
    # =====================================

    def initialize(
        self,
        item,
        device,
        width,
        height
    ):


        self.item = item

        self.device = device



        print(
            "Creando tamaño WinRT"
        )


        size = foundation.Size(
            width,
            height
        )


        print(
            "Tamaño captura:",
            size.width,
            "x",
            size.height
        )



        print(
            "Creando FramePool"
        )


        self.frame_pool = (
            capture
            .Direct3D11CaptureFramePool
            .create_free_threaded(

                self.device,

                directx
                .DirectXPixelFormat
                .B8_G8_R8_A8_UINT_NORMALIZED,

                2,

                size

            )
        )


        print(
            "FramePool creado"
        )



        self.session = (
            self.frame_pool
            .create_capture_session(
                self.item
            )
        )


        print(
            "Session creada"
        )



        self.session.start_capture()


        print(
            "Captura iniciada"
        )


        return True



    # =====================================
    # Obtener frame
    # =====================================

    def get_frame(
        self
    ):


        if self.frame_pool is None:

            return None


        return (
            self.frame_pool
            .try_get_next_frame()
        )



    # =====================================
    # Detener captura
    # =====================================

    def stop(
        self
    ):


        if self.session:

            self.session.close()



        if self.frame_pool:

            self.frame_pool.close()



        self.session = None

        self.frame_pool = None