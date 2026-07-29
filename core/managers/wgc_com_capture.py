import ctypes
import comtypes

from comtypes import GUID


# ==================================================
# GUID Windows Graphics Capture
# ==================================================

GraphicsCaptureItem_GUID = GUID(
    "{79C3F95B-31F7-4EC2-A464-632EF5D30760}"
)


IGraphicsCaptureItemInterop_GUID = GUID(
    "{3628E81B-3CAC-4C60-B7F4-23CE0E0C3356}"
)



# ==================================================
# Interface COM
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
                [
                    "in"
                ],
                ctypes.c_void_p
            ),

            (
                [
                    "in"
                ],
                ctypes.POINTER(
                    GUID
                )
            ),

            (
                [
                    "out"
                ],
                ctypes.POINTER(
                    ctypes.c_void_p
                )
            )
        )
    ]



# ==================================================
# Captura WGC COM
# ==================================================

class WGCComCapture:


    def __init__(
        self,
        hwnd
    ):

        self.hwnd = hwnd

        self.item = None



    # =====================================
    # Inicialización
    # =====================================

    def initialize(self):

        print(
            "Inicializando WGC COM"
        )


        comtypes.CoInitialize()


        print(
            "HWND:",
            self.hwnd
        )


        return self.create_capture_item()



    # =====================================
    # Crear GraphicsCaptureItem
    # =====================================

    def create_capture_item(self):


        try:


            factory = comtypes.CoCreateInstance(
                GraphicsCaptureItem_GUID,
                IGraphicsCaptureItemInterop,
                comtypes.CLSCTX_INPROC_SERVER
            )



            item = ctypes.c_void_p()



            result = factory.CreateForWindow(
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



            if result != 0:

                print(
                    "Error HRESULT:",
                    hex(result)
                )

                return False



            self.item = item



            print(
                "GraphicsCaptureItem creado correctamente"
            )


            return True



        except Exception as e:


            print(
                "Error creando GraphicsCaptureItem:"
            )

            print(
                e
            )


            return False