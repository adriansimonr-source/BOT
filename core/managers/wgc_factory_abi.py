import ctypes
import comtypes



RUNTIME_CLASS = (
    "Windows.Graphics.Capture.Direct3D11CaptureFramePool"
)



IID_FRAMEPOOL_STATICS2 = comtypes.GUID(
    "{589B103F-6BBC-5DF5-A991-02E28B3B66D5}"
)



class WGCFactoryABI:


    def get_statics2(self):


        print(
            "Obteniendo STATICS2"
        )


        combase = ctypes.windll.combase



        # ============================
        # Crear HSTRING
        # ============================

        combase.WindowsCreateString.argtypes = [

            ctypes.c_wchar_p,

            ctypes.c_uint32,

            ctypes.POINTER(
                ctypes.c_void_p
            )

        ]


        combase.WindowsCreateString.restype = ctypes.HRESULT



        hstring = ctypes.c_void_p()



        hr = combase.WindowsCreateString(

            RUNTIME_CLASS,

            len(RUNTIME_CLASS),

            ctypes.byref(
                hstring
            )

        )


        print(
            "WindowsCreateString:",
            hex(
                hr & 0xffffffff
            )
        )


        if hr != 0:

            raise OSError(
                hr,
                "WindowsCreateString fallo"
            )



        # ============================
        # RoGetActivationFactory
        # ============================


        statics2 = ctypes.c_void_p()



        RoGetActivationFactory = (
            combase.RoGetActivationFactory
        )


        RoGetActivationFactory.argtypes = [

            ctypes.c_void_p,

            ctypes.POINTER(
                comtypes.GUID
            ),

            ctypes.POINTER(
                ctypes.c_void_p
            )

        ]


        RoGetActivationFactory.restype = ctypes.HRESULT



        hr = RoGetActivationFactory(

            hstring,

            ctypes.byref(
                IID_FRAMEPOOL_STATICS2
            ),

            ctypes.byref(
                statics2
            )

        )



        print(
            "RoGetActivationFactory:",
            hex(
                hr & 0xffffffff
            )
        )



        # liberar HSTRING

        combase.WindowsDeleteString(
            hstring
        )



        if hr != 0:

            raise OSError(
                hr,
                "No se obtuvo STATICS2"
            )



        print(
            "STATICS2:",
            statics2
        )


        return statics2