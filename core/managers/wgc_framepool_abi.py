import ctypes


class WGCFramePoolABI:


    def __init__(self):

        self.statics2 = None



    def get_statics2(self):

        from core.managers.wgc_factory_abi import (
            WGCFactoryABI
        )


        factory = WGCFactoryABI()


        self.statics2 = (
            factory.get_framepool_statics2()
        )


        print(
            "STATICS2:",
            self.statics2
        )


        return self.statics2



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



        # IStatics2:
        #
        # 0 QueryInterface
        # 1 AddRef
        # 2 Release
        # 3 GetIids
        # 4 GetRuntimeClassName
        # 5 GetTrustLevel
        # 6 Create
        # 7 CreateFreeThreaded


        CreateFreeThreaded = ctypes.CFUNCTYPE(

            ctypes.c_long,

            ctypes.c_void_p,

            ctypes.c_void_p,

            ctypes.c_int,

            ctypes.c_int,

            ctypes.c_int,

            ctypes.POINTER(
                ctypes.c_void_p
            )

        )(

            vtable[7]

        )



        result = ctypes.c_void_p()



        hr = CreateFreeThreaded(

            self.statics2,

            device,

            87,        # B8G8R8A8_UNORM

            2,

            width,

            height,

            ctypes.byref(
                result
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
            result
        )


        return result