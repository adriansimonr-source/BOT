import ctypes

from core.managers.com_utils import get_vtable


class Direct3DContextManager:

    def __init__(self):
        self.context = None

    def create_context(self, device):
        get_immediate_context = ctypes.WINFUNCTYPE(
            None,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        )(get_vtable(device)[40])
        context = ctypes.c_void_p()
        get_immediate_context(device, ctypes.byref(context))
        if not context.value:
            raise RuntimeError("No se pudo obtener DeviceContext")
        self.context = context
        return context
