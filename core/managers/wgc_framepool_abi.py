import ctypes
import comtypes



RUNTIME_CLASS = (
    "Windows.Graphics.Capture.Direct3D11CaptureFramePool"
)



IActivationFactory_GUID = comtypes.GUID(
    "{00000035-0000-0000-C000-000000000046}"
)



class WGCFramePoolABI:


    def __init__(self):

        self.factory = None



    def get_factory(self):

        print(
            "Obteniendo IActivationFactory"
        )


        combase = ctypes.windll.combase


        RoGetActivationFactory = (
            combase.RoGetActivationFactory
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


        RoGetActivationFactory.restype = ctypes.HRESULT



        factory = ctypes.c_void_p()



        hr = RoGetActivationFactory(

            RUNTIME_CLASS,

            ctypes.byref(
                IActivationFactory_GUID
            ),

            ctypes.byref(
                factory
            )

        )


        if hr != 0:

            print(
                "HRESULT:",
                hex(hr)
            )

            return False



        self.factory = factory



        print(
            "IActivationFactory OK:",
            factory
        )


        return True



    def get_pointer(self):

        return self.factory