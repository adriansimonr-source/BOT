import ctypes
import comtypes

from comtypes import GUID


# ==================================================
# Windows Runtime
# ==================================================

combase = ctypes.windll.combase


RoGetActivationFactory = (
    combase.RoGetActivationFactory
)


RoGetActivationFactory.argtypes = [
    ctypes.c_wchar_p,
    ctypes.POINTER(GUID),
    ctypes.POINTER(ctypes.c_void_p)
]


RoGetActivationFactory.restype = ctypes.HRESULT



# ==================================================
# GUIDS
# ==================================================

IInspectable_GUID = GUID(
    "{AF86E2E0-B12D-4C6A-9C5A-D7AA65101E90}"
)


IGraphicsCaptureItemInterop_GUID = GUID(
    "{3628E81B-3CAC-4C60-B7F4-23CE0E0C3356}"
)


GraphicsCaptureItem_GUID = GUID(
    "{79C3F95B-31F7-4EC2-A464-632EF5D30760}"
)



RuntimeClass = (
    "Windows.Graphics.Capture.GraphicsCaptureItem"
)



# ==================================================
# COM Interface
# ==================================================

class IGraphicsCaptureItemInterop(
    comtypes.IUnknown
):

    _iid_ = IGraphicsCaptureItemInterop_GUID


    _methods_ = [

        comtypes.COMMETHOD(
            [],
            ctypes.HRESULT,
            "CreateForWindow",

            (
                ["in"],
                ctypes.c_void_p
            ),

            (
                ["in"],
                ctypes.POINTER(GUID)
            ),

            (
                ["out"],
                ctypes.POINTER(
                    ctypes.c_void_p
                )
            )
        )
    ]



# ==================================================
# Captura WGC
# ==================================================

class WGCComCapture:


    def __init__(
        self,
        hwnd
    ):

        self.hwnd = hwnd
        self.item = None



    def initialize(self):

        print(
            "Inicializando WGC COM"
        )


        comtypes.CoInitialize()


        print(
            "HWND:",
            self.hwnd
        )


        return self.create_item()



    def create_item(self):

        try:

            factory_ptr = ctypes.c_void_p()


            hr = RoGetActivationFactory(
                RuntimeClass,
                ctypes.byref(
                    IInspectable_GUID
                ),
                ctypes.byref(
                    factory_ptr
                )
            )


            if hr != 0:

                print(
                    "Factory error:",
                    hex(hr)
                )

                return False



            print(
                "Factory obtenida"
            )



            # Convertir factory a IUnknown

            unknown = ctypes.cast(
                factory_ptr,
                ctypes.POINTER(
                    comtypes.IUnknown
                )
            )



            interop = (
                unknown.QueryInterface(
                    IGraphicsCaptureItemInterop
                )
            )



            print(
                "Interop obtenida"
            )



            item = ctypes.c_void_p()



            hr = interop.CreateForWindow(
                ctypes.c_void_p(
                    self.hwnd
                ),
                ctypes.byref(
                    GraphicsCaptureItem_GUID
                ),
                ctypes.byref(
                    item
                )
            )



            if hr != 0:

                print(
                    "CreateForWindow HRESULT:",
                    hex(hr)
                )

                return False



            self.item = item



            print(
                "GraphicsCaptureItem creado correctamente"
            )


            return True



        except Exception as e:

            print(
                "Error WGC:"
            )

            print(
                e
            )


            return False