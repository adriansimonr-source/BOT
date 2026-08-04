import ctypes

import comtypes

from core.managers.com_utils import get_vtable, release_com


GRAPHICS_CAPTURE_ITEM_RUNTIME = (
    "Windows.Graphics.Capture.GraphicsCaptureItem"
)
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
        self.item = None

    def create_for_window(self, hwnd):
        combase = ctypes.windll.combase
        combase.WindowsCreateString.argtypes = [
            ctypes.c_wchar_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        combase.WindowsCreateString.restype = ctypes.HRESULT
        combase.WindowsDeleteString.argtypes = [ctypes.c_void_p]
        combase.WindowsDeleteString.restype = ctypes.HRESULT

        hstring = ctypes.c_void_p()
        factory = ctypes.c_void_p()
        interop = ctypes.c_void_p()
        hr = combase.WindowsCreateString(
            GRAPHICS_CAPTURE_ITEM_RUNTIME,
            len(GRAPHICS_CAPTURE_ITEM_RUNTIME),
            ctypes.byref(hstring),
        )
        if hr != 0:
            raise OSError(hr, "WindowsCreateString fallo")

        try:
            get_factory = combase.RoGetActivationFactory
            get_factory.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(comtypes.GUID),
                ctypes.POINTER(ctypes.c_void_p),
            ]
            get_factory.restype = ctypes.HRESULT
            hr = get_factory(
                hstring,
                ctypes.byref(IID_IINSPECTABLE),
                ctypes.byref(factory),
            )
            if hr != 0:
                raise OSError(hr, "RoGetActivationFactory fallo")

            query_interface = ctypes.WINFUNCTYPE(
                ctypes.HRESULT,
                ctypes.c_void_p,
                ctypes.POINTER(comtypes.GUID),
                ctypes.POINTER(ctypes.c_void_p),
            )(get_vtable(factory)[0])
            hr = query_interface(
                factory,
                ctypes.byref(IID_GRAPHICS_CAPTURE_ITEM_INTEROP),
                ctypes.byref(interop),
            )
            if hr != 0:
                raise OSError(hr, "No existe IGraphicsCaptureItemInterop")

            create_for_window = ctypes.WINFUNCTYPE(
                ctypes.HRESULT,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.POINTER(comtypes.GUID),
                ctypes.POINTER(ctypes.c_void_p),
            )(get_vtable(interop)[3])
            item = ctypes.c_void_p()
            hr = create_for_window(
                interop,
                ctypes.c_void_p(hwnd),
                ctypes.byref(IID_GRAPHICS_CAPTURE_ITEM),
                ctypes.byref(item),
            )
            if hr != 0:
                raise OSError(hr, "CreateForWindow fallo")
            self.item = item
            return item
        finally:
            if interop.value:
                release_com(interop)
            if factory.value:
                release_com(factory)
            combase.WindowsDeleteString(hstring)
