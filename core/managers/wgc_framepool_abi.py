import ctypes


from core.managers.wgc_factory_abi import (
    WGCFactoryABI
)



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



class WGCFramePoolABI:


    def __init__(self):

        self.statics2 = None



    # ======================================
    # Inicializar STATICS2
    # ======================================

    def get_statics2(self):


        factory = WGCFactoryABI()


        self.statics2 = (
            factory.get_statics2()
        )


        return self.statics2



    # ======================================
    # Crear FramePool FreeThreaded
    # ======================================

    def create_free_threaded(
        self,
        device,
        width,
        height
    ):


        if self.statics2 is None:

            raise RuntimeError(
                "Statics2 no inicializado"
            )



        print(
            "Creando FramePool FreeThreaded"
        )



        obj = ctypes.cast(

            self.statics2,

            ctypes.POINTER(
                ctypes.POINTER(
                    ctypes.c_void_p
                )
            )

        )


        vtable = obj.contents



        print(
            "VTABLE STATICS2"
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



        CreateFreeThreaded = ctypes.WINFUNCTYPE(

            ctypes.c_long,

            ctypes.c_void_p,     # this

            ctypes.c_void_p,     # IDirect3DDevice

            ctypes.c_int,        # PixelFormat

            ctypes.c_int,        # Buffers

            SizeInt32,           # Size

            ctypes.POINTER(
                ctypes.c_void_p
            )

        )(

            vtable[6]

        )



        framepool = ctypes.c_void_p()



        size = SizeInt32(

            width,

            height

        )



        DXGI_FORMAT_B8G8R8A8_UNORM = 87



        print(
            "STATICS2:",
            self.statics2
        )


        print(
            "DEVICE:",
            device
        )


        print(
            "SIZE:",
            size.Width,
            size.Height
        )



        hr = CreateFreeThreaded(

            self.statics2,

            device,

            DXGI_FORMAT_B8G8R8A8_UNORM,

            2,

            size,

            ctypes.byref(
                framepool
            )

        )



        print(
            "CreateFreeThreaded HRESULT:",
            hex(
                hr & 0xffffffff
            )
        )



        if hr != 0:

            raise OSError(
                hr,
                "CreateFreeThreaded fallo"
            )



        print(
            "FRAMEPOOL:",
            framepool
        )


        return framepool