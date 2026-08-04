import ctypes

import comtypes

from core.managers.com_utils import get_vtable, release_com


IID_IGRAPHICS_CAPTURE_SESSION3 = comtypes.GUID(
    "{F2CDD966-22AE-5EA1-9596-3A289344C3BE}"
)


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

    def try_disable_border(self):
        if self.session is None:
            return False

        session3 = None
        try:
            session3 = self._query_border_session()
            if session3 is None:
                return False
            return self._set_border_required(session3, False)
        except (OSError, TypeError, ValueError):
            return False
        finally:
            if session3 is not None:
                release_com(session3)

    def _query_border_session(self):
        query_interface = ctypes.WINFUNCTYPE(
            ctypes.HRESULT,
            ctypes.c_void_p,
            ctypes.POINTER(comtypes.GUID),
            ctypes.POINTER(ctypes.c_void_p),
        )(get_vtable(self.session)[0])
        session3 = ctypes.c_void_p()
        hr = query_interface(
            self.session,
            ctypes.byref(IID_IGRAPHICS_CAPTURE_SESSION3),
            ctypes.byref(session3),
        )
        if hr != 0 or not session3.value:
            return None
        return session3

    @staticmethod
    def _set_border_required(session3, required):
        setter = ctypes.WINFUNCTYPE(
            ctypes.HRESULT,
            ctypes.c_void_p,
            ctypes.c_ubyte,
        )(get_vtable(session3)[7])
        return setter(session3, int(bool(required))) == 0
