import ctypes





# ==================================================
# D3D11_MAPPED_SUBRESOURCE
# ==================================================

class D3D11MappedSubresource(ctypes.Structure):

    _fields_ = [

        (
            "pData",
            ctypes.c_void_p
        ),

        (
            "RowPitch",
            ctypes.c_uint32
        ),

        (
            "DepthPitch",
            ctypes.c_uint32
        )

    ]







class Direct3DMapManager:


    def __init__(self):

        self.context = None





    # ==================================================
    # Asignar DeviceContext
    # ==================================================

    def set_context(

        self,

        context

    ):

        self.context = context






    # ==================================================
    # Map staging texture
    # ==================================================

    def map_texture(

        self,

        texture

    ):


        if self.context is None:

            raise RuntimeError(
                "No existe DeviceContext"
            )



        print(
            "Mapeando staging texture"
        )





        # Obtener vtable Context

        obj = ctypes.cast(

            self.context,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        vtable = obj.contents






        #
        # ID3D11DeviceContext
        #
        # Map:
        #
        # índice 14
        #
        # HRESULT Map(
        #   ID3D11Resource* pResource,
        #   UINT Subresource,
        #   D3D11_MAP MapType,
        #   UINT MapFlags,
        #   D3D11_MAPPED_SUBRESOURCE*
        # )
        #
        # ABI:
        #
        # this,
        # resource,
        # subresource,
        # mapType,
        # flags,
        # mapped
        #



        Map = ctypes.WINFUNCTYPE(

            ctypes.c_long,

            ctypes.c_void_p,   # this

            ctypes.c_void_p,   # resource

            ctypes.c_uint32,   # subresource

            ctypes.c_uint32,   # map type

            ctypes.c_uint32,   # flags

            ctypes.POINTER(
                D3D11MappedSubresource
            )

        )(

            vtable[14]

        )





        mapped = D3D11MappedSubresource()






        # D3D11_MAP_READ

        D3D11_MAP_READ = 1



        hr = Map(

            self.context,

            texture,

            0,

            D3D11_MAP_READ,

            0,

            ctypes.byref(
                mapped
            )

        )





        print(

            "Map HRESULT:",

            hex(
                hr & 0xffffffff
            )

        )





        if hr != 0:


            raise OSError(

                hr,

                "Map fallo"

            )






        print()

        print(
            "=============================="
        )

        print(
            "MAP RESULT"
        )

        print(
            "=============================="
        )



        print(

            "pData:",

            mapped.pData

        )


        print(

            "RowPitch:",

            mapped.RowPitch

        )


        print(

            "DepthPitch:",

            mapped.DepthPitch

        )





        return mapped








    # ==================================================
    # Unmap
    # ==================================================

    def unmap_texture(

        self,

        texture

    ):


        if self.context is None:

            return





        obj = ctypes.cast(

            self.context,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        vtable = obj.contents






        #
        # Unmap
        #
        # índice 15
        #



        Unmap = ctypes.WINFUNCTYPE(

            None,

            ctypes.c_void_p,

            ctypes.c_void_p,

            ctypes.c_uint32

        )(

            vtable[15]

        )





        Unmap(

            self.context,

            texture,

            0

        )



        print(
            "Texture liberada"
        )