import ctypes

import comtypes

from core.managers.com_utils import get_vtable, release_com


IID_IDXGI_DEVICE = comtypes.GUID(
    "{54EC77FA-1377-44E6-8C32-88FD5F44C84C}"
)


class Direct3DConverter:

    def __init__(self):
        self.winrt_device = None

    def create_winrt_device(self, d3d_device):
        query_interface = ctypes.WINFUNCTYPE(
            ctypes.HRESULT,
            ctypes.c_void_p,
            ctypes.POINTER(comtypes.GUID),
            ctypes.POINTER(ctypes.c_void_p),
        )(get_vtable(d3d_device)[0])
        dxgi_device = ctypes.c_void_p()
        hr = query_interface(
            d3d_device,
            ctypes.byref(IID_IDXGI_DEVICE),
            ctypes.byref(dxgi_device),
        )
        if hr != 0:
            return False

        try:
            create_device = ctypes.windll.d3d11.CreateDirect3D11DeviceFromDXGIDevice
            create_device.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_void_p),
            ]
            create_device.restype = ctypes.HRESULT
            winrt_device = ctypes.c_void_p()
            hr = create_device(dxgi_device, ctypes.byref(winrt_device))
            if hr != 0:
                return False
            self.winrt_device = winrt_device
            return True
        finally:
            release_com(dxgi_device)

    def get_device(self):
        return self.winrt_device
