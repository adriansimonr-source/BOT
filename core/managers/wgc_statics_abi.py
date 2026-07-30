import ctypes
import comtypes


RUNTIME_CLASS = (
    "Windows.Graphics.Capture.Direct3D11CaptureFramePool"
)


IINSPECTABLE = comtypes.GUID(
    "{AF86E2E0-B12D-4C6A-9C5A-D7AA65101E90}"
)



class WGCStaticsABI:


    def get_factory(self):

        print(
            "RoGetActivationFactory"
        )


        factory = ctypes.c_void_p()


        RoGetActivationFactory = (
            ctypes.windll.combase
            .RoGetActivationFactory
        )


        RoGetActivationFactory.argtypes = [

            ctypes.c_wchar_p,

            ctypes.POINTER(
                comtypes.GUID
            ),

            ctypes.POINTER(
                ctypes.c_void_p
            )

        ]


        RoGetActivationFactory.restype = (
            ctypes.HRESULT
        )


        hr = RoGetActivationFactory(

            RUNTIME_CLASS,

            ctypes.byref(
                IINSPECTABLE
            ),

            ctypes.byref(
                factory
            )

        )


        print(
            "HRESULT:",
            hex(hr)
        )

        print(
            "FACTORY:",
            factory
        )


        return factory