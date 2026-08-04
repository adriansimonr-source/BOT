import ctypes

from core.managers.com_utils import close_winrt, release_com


class WGCFrameABI:

    def __init__(self):
        self.frame = None
        self._get_surface = None

    def set_frame(self, frame):
        self.frame = frame

    def get_surface(self):
        if self.frame is None:
            raise RuntimeError("No hay frame asignado")

        if self._get_surface is None:
            vtable = ctypes.cast(
                self.frame,
                ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)),
            ).contents
            self._get_surface = ctypes.WINFUNCTYPE(
                ctypes.HRESULT,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_void_p),
            )(vtable[6])

        surface = ctypes.c_void_p()
        hr = self._get_surface(self.frame, ctypes.byref(surface))
        if hr != 0:
            raise OSError(hr, "Surface fallo")
        return surface

    def release_surface(self, surface):
        if not surface:
            return
        close_winrt(surface)
        release_com(surface)
