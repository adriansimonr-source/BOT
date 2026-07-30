import ctypes




# ==================================================
# D3D11_TEXTURE2D_DESC
# ==================================================

class D3D11_TEXTURE2D_DESC(ctypes.Structure):

    _fields_ = [

        (
            "Width",
            ctypes.c_uint32
        ),

        (
            "Height",
            ctypes.c_uint32
        ),

        (
            "MipLevels",
            ctypes.c_uint32
        ),

        (
            "ArraySize",
            ctypes.c_uint32
        ),

        (
            "Format",
            ctypes.c_uint32
        ),

        (
            "SampleDescCount",
            ctypes.c_uint32
        ),

        (
            "SampleDescQuality",
            ctypes.c_uint32
        ),

        (
            "Usage",
            ctypes.c_uint32
        ),

        (
            "BindFlags",
            ctypes.c_uint32
        ),

        (
            "CPUAccessFlags",
            ctypes.c_uint32
        ),

        (
            "MiscFlags",
            ctypes.c_uint32
        )

    ]





class D3D11TextureManager:


    def __init__(self):

        self.texture = None





    # ==================================================
    # Asignar textura
    # ==================================================

    def set_texture(
        self,
        texture
    ):

        self.texture = texture






    # ==================================================
    # Obtener descripción Texture2D
    # ==================================================

    def get_desc(
        self
    ):


        if self.texture is None:

            raise RuntimeError(
                "No hay textura"
            )



        obj = ctypes.cast(

            self.texture,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        vtable = obj.contents




        # ==============================================
        # Debug VTable
        # ==============================================

        print()

        print(
            "VTABLE TEXTURE"
        )


        for i in range(20):

            print(

                i,

                hex(

                    ctypes.cast(

                        vtable[i],

                        ctypes.c_void_p

                    ).value

                )

            )





        # ==============================================
        # ID3D11Texture2D::GetDesc
        #
        # índice confirmado:
        #
        # 10
        #
        # ==============================================


        GetDesc = ctypes.WINFUNCTYPE(

            None,

            ctypes.c_void_p,

            ctypes.POINTER(
                D3D11_TEXTURE2D_DESC
            )

        )(

            vtable[10]

        )



        desc = D3D11_TEXTURE2D_DESC()



        GetDesc(

            self.texture,

            ctypes.byref(
                desc
            )

        )





        print()

        print(
            "=============================="
        )

        print(
            "TEXTURE DESC"
        )

        print(
            "=============================="
        )


        print(
            "Width:",
            desc.Width
        )


        print(
            "Height:",
            desc.Height
        )


        print(
            "Format:",
            desc.Format
        )


        print(
            "MipLevels:",
            desc.MipLevels
        )


        print(
            "ArraySize:",
            desc.ArraySize
        )


        print(
            "Usage:",
            desc.Usage
        )


        print(
            "BindFlags:",
            hex(
                desc.BindFlags
            )
        )


        print(
            "CPUAccessFlags:",
            hex(
                desc.CPUAccessFlags
            )
        )


        print(
            "MiscFlags:",
            hex(
                desc.MiscFlags
            )
        )


        print(
            "=============================="
        )



        return desc