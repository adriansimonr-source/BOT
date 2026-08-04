import ctypes

import comtypes


RUNTIME_CLASS = "Windows.Graphics.Capture.Direct3D11CaptureFramePool"
IID_FRAMEPOOL_STATICS2 = comtypes.GUID(
    "{589B103F-6BBC-5DF5-A991-02E28B3B66D5}"
)


class WGCFactoryABI:

    def get_statics2(self):
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
        hr = combase.WindowsCreateString(
            RUNTIME_CLASS,
            len(RUNTIME_CLASS),
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
            statics = ctypes.c_void_p()
            hr = get_factory(
                hstring,
                ctypes.byref(IID_FRAMEPOOL_STATICS2),
                ctypes.byref(statics),
            )
            if hr != 0:
                raise OSError(hr, "No se obtuvo STATICS2")
            return statics
        finally:
            combase.WindowsDeleteString(hstring)
