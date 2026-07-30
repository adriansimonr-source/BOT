import ctypes
import comtypes



# ==================================================
# GUIDS
# ==================================================

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



    # ==================================================
    # Surface -> DXGI Access
    # ==================================================

    def get_dxgi_access(
        self,
        surface
    ):


        print(
            "Obteniendo DXGI Access"
        )


        obj = ctypes.cast(

            surface,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        vtable = obj.contents



        QueryInterface = ctypes.WINFUNCTYPE(

            ctypes.HRESULT,

            ctypes.c_void_p,

            ctypes.POINTER(
                comtypes.GUID
            ),

            ctypes.POINTER(
                ctypes.c_void_p
            )

        )(

            vtable[0]

        )



        access = ctypes.c_void_p()



        hr = QueryInterface(

            surface,

            ctypes.byref(
                IID_IDIRECT3DDXGI_INTERFACE_ACCESS
            ),

            ctypes.byref(
                access
            )

        )



        print(
            "DXGI Access HRESULT:",
            hex(
                hr & 0xffffffff
            )
        )



        if hr != 0:

            raise OSError(
                hr,
                "No existe DXGI Access"
            )



        self.access = access



        print(
            "DXGI ACCESS:",
            access
        )


        return access





    # ==================================================
    # DXGI Access -> ID3D11Texture2D
    # ==================================================

    def get_texture(
        self,
        access
    ):


        print(
            "Obteniendo ID3D11Texture2D"
        )



        obj = ctypes.cast(

            access,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        vtable = obj.contents



        print(
            "VTABLE DXGI ACCESS"
        )


        for i in range(5):

            print(

                i,

                hex(

                    ctypes.cast(

                        vtable[i],

                        ctypes.c_void_p

                    ).value

                )

            )



        GetInterface = ctypes.WINFUNCTYPE(

            ctypes.HRESULT,

            ctypes.c_void_p,

            ctypes.POINTER(
                comtypes.GUID
            ),

            ctypes.POINTER(
                ctypes.c_void_p
            )

        )(

            vtable[3]

        )



        texture = ctypes.c_void_p()



        hr = GetInterface(

            access,

            ctypes.byref(
                IID_ID3D11_TEXTURE2D
            ),

            ctypes.byref(
                texture
            )

        )



        print(
            "GetInterface HRESULT:",
            hex(
                hr & 0xffffffff
            )
        )



        if hr != 0:

            raise OSError(
                hr,
                "No se pudo obtener Texture2D"
            )



        self.texture = texture



        print(
            "TEXTURE:",
            texture
        )



        return texture