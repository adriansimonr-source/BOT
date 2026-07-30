import ctypes



class WGCSessionABI:


    def __init__(self):

        self.session = None



    # ==================================================
    # Crear GraphicsCaptureSession
    # ==================================================

    def create_session(
        self,
        framepool,
        item
    ):


        print(
            "Creando GraphicsCaptureSession"
        )


        # Obtener vtable del FramePool

        obj = ctypes.cast(

            framepool,

            ctypes.POINTER(
                ctypes.POINTER(
                    ctypes.c_void_p
                )
            )

        )


        vtable = obj.contents



        print(
            "VTABLE FRAMEPOOL"
        )


        for i in range(12):

            print(
                i,
                hex(
                    ctypes.cast(
                        vtable[i],
                        ctypes.c_void_p
                    ).value
                )
            )



        #
        # IDirect3D11CaptureFramePool : IInspectable
        #
        # 0 QueryInterface
        # 1 AddRef
        # 2 Release
        # 3 GetIids
        # 4 GetRuntimeClassName
        # 5 GetTrustLevel
        #
        # 6 Recreate
        # 7 TryGetNextFrame
        # 8 FrameArrived add
        # 9 FrameArrived remove
        # 10 CreateCaptureSession
        # 11 DispatcherQueue
        #



        CreateCaptureSession = ctypes.CFUNCTYPE(

            ctypes.c_long,

            ctypes.c_void_p,       # this

            ctypes.c_void_p,       # GraphicsCaptureItem

            ctypes.POINTER(
                ctypes.c_void_p
            )

        )(

            vtable[10]

        )



        session = ctypes.c_void_p()



        hr = CreateCaptureSession(

            framepool,

            item,

            ctypes.byref(
                session
            )

        )



        print(
            "CreateCaptureSession HRESULT:",
            hex(
                hr & 0xffffffff
            )
        )



        if hr != 0:

            raise OSError(
                hr,
                "CreateCaptureSession fallo"
            )



        print(
            "SESSION:",
            session
        )



        self.session = session



        return session





    # ==================================================
    # StartCapture
    # ==================================================

    def start_capture(
        self
    ):


        if self.session is None:

            raise RuntimeError(
                "No existe session"
            )



        obj = ctypes.cast(

            self.session,

            ctypes.POINTER(
                ctypes.POINTER(
                    ctypes.c_void_p
                )
            )

        )


        vtable = obj.contents



        print(
            "VTABLE SESSION"
        )


        for i in range(8):

            print(
                i,
                hex(
                    ctypes.cast(
                        vtable[i],
                        ctypes.c_void_p
                    ).value
                )
            )



        #
        # IGraphicsCaptureSession : IInspectable
        #
        # 0 QueryInterface
        # 1 AddRef
        # 2 Release
        # 3 GetIids
        # 4 GetRuntimeClassName
        # 5 GetTrustLevel
        # 6 StartCapture
        #



        StartCapture = ctypes.CFUNCTYPE(

            ctypes.c_long,

            ctypes.c_void_p

        )(

            vtable[6]

        )



        print(
            "Ejecutando StartCapture"
        )



        hr = StartCapture(

            self.session

        )



        print(
            "StartCapture HRESULT:",
            hex(
                hr & 0xffffffff
            )
        )



        if hr != 0:

            raise OSError(
                hr,
                "StartCapture fallo"
            )



        print(
            "CAPTURA INICIADA"
        )