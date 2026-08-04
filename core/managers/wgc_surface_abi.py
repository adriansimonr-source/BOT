import ctypes

import comtypes


IID_IDIRECT3DDXGI_INTERFACE_ACCESS = comtypes.GUID(
    "{A9B3D012-3DF2-4EE3-B8D1-8695F457D3C1}"
)
IID_ID3D11_TEXTURE2D = comtypes.GUID(
    "{6F15AAF2-D208-4E89-9AB4-489535D34F9C}"
)


class WGCSurfaceABI:

    def __init__(self):
        self.access = None
        self.texture = None
        self._query_interface = None
        self._get_interface = None
        self._release_functions = {}

    @staticmethod
    def _vtable(interface):
        return ctypes.cast(
            interface,
            ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)),
        ).contents

    def get_dxgi_access(self, surface):
        if self._query_interface is None:
            self._query_interface = ctypes.WINFUNCTYPE(
                ctypes.HRESULT,
                ctypes.c_void_p,
                ctypes.POINTER(comtypes.GUID),
                ctypes.POINTER(ctypes.c_void_p),
            )(self._vtable(surface)[0])

        access = ctypes.c_void_p()
        hr = self._query_interface(
            surface,
            ctypes.byref(IID_IDIRECT3DDXGI_INTERFACE_ACCESS),
            ctypes.byref(access),
        )
        if hr != 0:
            raise OSError(hr, "No existe DXGI Access")
        self.access = access
        return access

    def get_texture(self, access):
        if self._get_interface is None:
            self._get_interface = ctypes.WINFUNCTYPE(
                ctypes.HRESULT,
                ctypes.c_void_p,
                ctypes.POINTER(comtypes.GUID),
                ctypes.POINTER(ctypes.c_void_p),
            )(self._vtable(access)[3])

        texture = ctypes.c_void_p()
        hr = self._get_interface(
            access,
            ctypes.byref(IID_ID3D11_TEXTURE2D),
            ctypes.byref(texture),
        )
        if hr != 0:
            raise OSError(hr, "No se pudo obtener Texture2D")
        self.texture = texture
        return texture

    def release_interface(self, interface):
        if not interface:
            return
        address = ctypes.cast(self._vtable(interface)[2], ctypes.c_void_p).value
        release = self._release_functions.get(address)
        if release is None:
            release = ctypes.WINFUNCTYPE(
                ctypes.c_ulong,
                ctypes.c_void_p,
            )(address)
            self._release_functions[address] = release
        release(interface)
        if interface is self.access:
            self.access = None
        if interface is self.texture:
            self.texture = None
