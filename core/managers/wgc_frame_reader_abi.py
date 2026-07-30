import ctypes


class WGCFrameReaderABI:


    def __init__(self):

        self.framepool = None



    def set_framepool(
        self,
        framepool
    ):

        self.framepool = framepool



    # ==================================================
    # TryGetNextFrame
    # ==================================================

    def try_get_frame(
        self
    ):


        if self.framepool is None:

            raise RuntimeError(
                "FramePool no configurado"
            )



        obj = ctypes.cast(

            self.framepool,

            ctypes.POINTER(
                ctypes.POINTER(
                    ctypes.c_void_p
                )
            )

        )


        vtable = obj.contents



        #
        # IDirect3D11CaptureFramePool
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



        TryGetNextFrame = ctypes.CFUNCTYPE(

            ctypes.c_long,

            ctypes.c_void_p,

            ctypes.POINTER(
                ctypes.c_void_p
            )

        )(

            vtable[7]

        )



        frame = ctypes.c_void_p()



        hr = TryGetNextFrame(

            self.framepool,

            ctypes.byref(
                frame
            )

        )



        if hr != 0:

            print(
                "TryGetNextFrame HRESULT:",
                hex(
                    hr & 0xffffffff
                )
            )

            return None



        if not frame.value:

            return None



        print(
            "FRAME RECIBIDO:",
            frame
        )


        return frame