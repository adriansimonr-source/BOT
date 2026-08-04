import ctypes


class D3D11MappedSubresource(ctypes.Structure):
    _fields_ = [
        ("pData", ctypes.c_void_p),
        ("RowPitch", ctypes.c_uint32),
        ("DepthPitch", ctypes.c_uint32),
    ]


class Direct3DMapManager:

    D3D11_MAP_READ = 1

    def __init__(self):
        self.context = None
        self._map = None
        self._unmap = None

    def set_context(self, context):
        self.context = context
        self._map = None
        self._unmap = None
        if context:
            vtable = ctypes.cast(
                context,
                ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)),
            ).contents
            self._map = ctypes.WINFUNCTYPE(
                ctypes.c_long,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.c_uint32,
                ctypes.POINTER(D3D11MappedSubresource),
            )(vtable[14])
            self._unmap = ctypes.WINFUNCTYPE(
                None,
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_uint32,
            )(vtable[15])

    def map_texture(self, texture):
        if self.context is None or self._map is None:
            raise RuntimeError("No existe DeviceContext")

        mapped = D3D11MappedSubresource()
        hr = self._map(
            self.context,
            texture,
            0,
            self.D3D11_MAP_READ,
            0,
            ctypes.byref(mapped),
        )
        if hr != 0:
            raise OSError(hr, "Map fallo")
        return mapped

    def unmap_texture(self, texture):
        if self.context is not None and self._unmap is not None:
            self._unmap(self.context, texture, 0)
