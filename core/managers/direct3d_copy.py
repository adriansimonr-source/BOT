import ctypes


class Direct3DCopyManager:

    def __init__(self):
        self.context = None
        self._copy_resource = None

    def set_context(self, context):
        self.context = context
        self._copy_resource = None
        if context:
            vtable = ctypes.cast(
                context,
                ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)),
            ).contents
            self._copy_resource = ctypes.WINFUNCTYPE(
                None,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_void_p,
            )(vtable[47])

    def copy_resource(self, destination, source):
        if self.context is None or self._copy_resource is None:
            raise RuntimeError("No hay DeviceContext")
        self._copy_resource(self.context, destination, source)
        return True
