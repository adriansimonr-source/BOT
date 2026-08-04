import ctypes

from core.managers.com_utils import get_vtable


class WGCSessionABI:

    def __init__(self):
        self.session = None

    def create_session(self, framepool, item):
        create_session = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        )(get_vtable(framepool)[10])
        session = ctypes.c_void_p()
        hr = create_session(
            framepool,
            item,
            ctypes.byref(session),
        )
        if hr != 0:
            raise OSError(hr, "CreateCaptureSession fallo")
        self.session = session
        return session

    def start_capture(self):
        if self.session is None:
            raise RuntimeError("No existe session")
        start_capture = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_void_p,
        )(get_vtable(self.session)[6])
        hr = start_capture(self.session)
        if hr != 0:
            raise OSError(hr, "StartCapture fallo")
