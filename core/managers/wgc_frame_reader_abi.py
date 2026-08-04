import ctypes

from core.managers.com_utils import close_winrt, release_com


class WGCFrameReaderABI:

    def __init__(self):
        self.framepool = None
        self._try_get_next_frame = None

    def set_framepool(self, framepool):
        self.framepool = framepool
        self._try_get_next_frame = None
        if framepool:
            vtable = ctypes.cast(
                framepool,
                ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)),
            ).contents
            self._try_get_next_frame = ctypes.WINFUNCTYPE(
                ctypes.c_long,
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.c_void_p),
            )(vtable[7])

    def try_get_next_frame(self):
        if self.framepool is None or self._try_get_next_frame is None:
            raise RuntimeError("FramePool no asignado")

        frame = ctypes.c_void_p()
        hr = self._try_get_next_frame(
            self.framepool,
            ctypes.byref(frame),
        )
        if hr != 0:
            raise OSError(hr, "TryGetNextFrame fallo")
        return frame if frame.value else None

    def release_frame(self, frame):
        if not frame:
            return
        close_winrt(frame)
        release_com(frame)
