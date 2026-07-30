import ctypes



class SizeInt32(ctypes.Structure):

    _fields_ = [

        (
            "Width",
            ctypes.c_int32
        ),

        (
            "Height",
            ctypes.c_int32
        )

    ]





class WGCFrameABI:


    def __init__(self):

        self.frame = None




    # ======================================
    # Asignar frame
    # ======================================

    def set_frame(
        self,
        frame
    ):

        self.frame = frame





    # ======================================
    # Obtener Surface
    # ======================================

    def get_surface(
        self
    ):


        if self.frame is None:

            raise RuntimeError(
                "No hay frame asignado"
            )



        obj = ctypes.cast(

            self.frame,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        vtable = obj.contents



        print(
            "VTABLE FRAME"
        )


        for i in range(10):

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
        # IDirect3D11CaptureFrame
        #
        # 0 QueryInterface
        # 1 AddRef
        # 2 Release
        # 3 GetIids
        # 4 GetRuntimeClassName
        # 5 GetTrustLevel
        # 6 Surface
        # 7 ContentSize
        #



        Surface = ctypes.WINFUNCTYPE(

            ctypes.HRESULT,

            ctypes.c_void_p,

            ctypes.POINTER(
                ctypes.c_void_p
            )

        )(

            vtable[6]

        )



        surface = ctypes.c_void_p()



        hr = Surface(

            self.frame,

            ctypes.byref(
                surface
            )

        )



        print(

            "Surface HRESULT:",

            hex(
                hr & 0xffffffff
            )

        )



        if hr != 0:

            raise OSError(

                hr,

                "Surface fallo"

            )



        print(

            "SURFACE:",

            surface

        )



        return surface

    def release_surface(

        self,

        surface

    ):


        if surface is None:

            return



        obj = ctypes.cast(

            surface,

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

            surface

        )