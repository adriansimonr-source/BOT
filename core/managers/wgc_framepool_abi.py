import ctypes

from core.managers.com_utils import get_vtable, release_com
from core.managers.wgc_factory_abi import WGCFactoryABI


class SizeInt32(ctypes.Structure):
    _fields_ = [
        ("Width", ctypes.c_int32),
        ("Height", ctypes.c_int32),
    ]


class WGCFramePoolABI:

    DXGI_FORMAT_B8G8R8A8_UNORM = 87

    def __init__(self):
        self.statics2 = None

    def get_statics2(self):
        self.statics2 = WGCFactoryABI().get_statics2()
        return self.statics2

    def create_free_threaded(self, device, width, height):
        if self.statics2 is None:
            raise RuntimeError("Statics2 no inicializado")

        create_free_threaded = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            SizeInt32,
            ctypes.POINTER(ctypes.c_void_p),
        )(get_vtable(self.statics2)[6])
        framepool = ctypes.c_void_p()
        try:
            hr = create_free_threaded(
                self.statics2,
                device,
                self.DXGI_FORMAT_B8G8R8A8_UNORM,
                2,
                SizeInt32(int(width), int(height)),
                ctypes.byref(framepool),
            )
        finally:
            release_com(self.statics2)
            self.statics2 = None
        if hr != 0:
            raise OSError(hr, "CreateFreeThreaded fallo")
        return framepool
