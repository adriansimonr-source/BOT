import ctypes



class WGCFrameReaderABI:


    def __init__(self):

        self.framepool = None



    # ======================================
    # Asignar FramePool
    # ======================================

    def set_framepool(
        self,
        framepool
    ):

        self.framepool = framepool




    # ======================================
    # Obtener siguiente frame
    # ======================================

    def try_get_next_frame(
        self
    ):


        if self.framepool is None:

            raise RuntimeError(
                "FramePool no asignado"
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



        TryGetNextFrame = ctypes.WINFUNCTYPE(

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

            raise OSError(

                hr,

                "TryGetNextFrame fallo"

            )



        if not frame.value:

            return None



        return frame





    # ======================================
    # Liberar Frame COM
    # ======================================

    def release_frame(

        self,

        frame

    ):


        if frame is None:

            return



        obj = ctypes.cast(

            frame,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        vtable = obj.contents



        Release = ctypes.WINFUNCTYPE(

            ctypes.c_ulong,

            ctypes.c_void_p

        )(

            vtable[2]

        )



        Release(

            frame

        )