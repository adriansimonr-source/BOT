import ctypes
import comtypes



# ==================================================
# Runtime Class
# ==================================================

GRAPHICS_CAPTURE_ITEM_RUNTIME = (
    "Windows.Graphics.Capture.GraphicsCaptureItem"
)



# ==================================================
# Interfaces
# ==================================================

IID_GRAPHICS_CAPTURE_ITEM_INTEROP = comtypes.GUID(
    "{3628E81B-3CAC-4C60-B7F4-23CE0E0C3356}"
)


IID_GRAPHICS_CAPTURE_ITEM = comtypes.GUID(
    "{79C3F95B-31F7-4EC2-A464-632EF5D30760}"
)


IID_IINSPECTABLE = comtypes.GUID(
    "{AF86E2E0-B12D-4C6A-9C5A-D7AA65101E90}"
)



class WGCItemABI:


    def __init__(self):

        self.factory = None
        self.interop = None
        self.item = None



    # ==================================================
    # Crear GraphicsCaptureItem desde HWND
    # ==================================================

    def create_for_window(
        self,
        hwnd
    ):


        print(
            "Creando GraphicsCaptureItem"
        )


        combase = ctypes.windll.combase



        # ==================================================
        # Crear HSTRING
        # ==================================================

        combase.WindowsCreateString.argtypes = [

            ctypes.c_wchar_p,

            ctypes.c_uint32,

            ctypes.POINTER(
                ctypes.c_void_p
            )

        ]


        combase.WindowsCreateString.restype = (
            ctypes.HRESULT
        )


        hstring = ctypes.c_void_p()



        hr = combase.WindowsCreateString(

            GRAPHICS_CAPTURE_ITEM_RUNTIME,

            len(
                GRAPHICS_CAPTURE_ITEM_RUNTIME
            ),

            ctypes.byref(
                hstring
            )

        )


        if hr != 0:

            raise OSError(
                hr,
                "WindowsCreateString fallo"
            )



        # ==================================================
        # Obtener Activation Factory
        # ==================================================

        factory = ctypes.c_void_p()



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


        RoGetActivationFactory.restype = (
            ctypes.HRESULT
        )



        hr = RoGetActivationFactory(

            hstring,

            ctypes.byref(
                IID_IINSPECTABLE
            ),

            ctypes.byref(
                factory
            )

        )



        print(
            "Factory:",
            factory
        )



        if hr != 0:

            raise OSError(
                hr,
                "RoGetActivationFactory fallo"
            )



        self.factory = factory



        # ==================================================
        # QueryInterface IGraphicsCaptureItemInterop
        # ==================================================

        obj = ctypes.cast(

            factory,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        vtable = obj.contents



        QueryInterface = ctypes.WINFUNCTYPE(

            ctypes.HRESULT,

            ctypes.c_void_p,

            ctypes.POINTER(
                comtypes.GUID
            ),

            ctypes.POINTER(
                ctypes.c_void_p
            )

        )(

            vtable[0]

        )



        interop = ctypes.c_void_p()



        hr = QueryInterface(

            factory,

            ctypes.byref(
                IID_GRAPHICS_CAPTURE_ITEM_INTEROP
            ),

            ctypes.byref(
                interop
            )

        )



        print(
            "Interop:",
            interop
        )



        if hr != 0:

            raise OSError(
                hr,
                "No existe IGraphicsCaptureItemInterop"
            )



        self.interop = interop



        # ==================================================
        # Obtener vtable Interop
        # ==================================================

        obj = ctypes.cast(

            interop,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        vtable = obj.contents



        print(
            "VTABLE ITEM INTEROP"
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



        # ==================================================
        # CreateForWindow
        #
        # IGraphicsCaptureItemInterop:
        #
        # 0 QueryInterface
        # 1 AddRef
        # 2 Release
        # 3 CreateForWindow
        # 4 CreateForMonitor
        #
        # ==================================================

        CreateForWindow = ctypes.WINFUNCTYPE(

            ctypes.HRESULT,

            ctypes.c_void_p,       # this

            ctypes.c_void_p,       # HWND

            ctypes.POINTER(
                comtypes.GUID
            ),                     # IID

            ctypes.POINTER(
                ctypes.c_void_p
            )

        )(

            vtable[3]

        )



        item = ctypes.c_void_p()



        hr = CreateForWindow(

            interop,

            ctypes.c_void_p(
                hwnd
            ),

            ctypes.byref(
                IID_GRAPHICS_CAPTURE_ITEM
            ),

            ctypes.byref(
                item
            )

        )



        print(
            "CreateForWindow HRESULT:",
            hex(
                hr & 0xffffffff
            )
        )



        if hr != 0:

            raise OSError(
                hr,
                "CreateForWindow fallo"
            )



        print(
            "ITEM:",
            item
        )



        self.item = item



        return item