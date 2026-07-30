import ctypes





class Direct3DCopyManager:


    def __init__(self):

        self.context = None





    # ==========================================
    # Asignar Context
    # ==========================================

    def set_context(

        self,

        context

    ):

        self.context = context





    # ==========================================
    # CopyResource
    # ==========================================

    def copy_resource(

        self,

        destination,

        source

    ):


        if self.context is None:

            raise RuntimeError(
                "No hay DeviceContext"
            )



        print(
            "Copiando recurso GPU -> STAGING"
        )



        obj = ctypes.cast(

            self.context,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        vtable = obj.contents





        print(
            "VTABLE CONTEXT"
        )


        for i in range(60):

            ptr = ctypes.cast(

                vtable[i],

                ctypes.c_void_p

            ).value


            print(

                i,

                hex(ptr)

            )





        #
        # ID3D11DeviceContext
        #
        # CopyResource
        #
        # índice esperado: 47
        #
        

        CopyResource = ctypes.WINFUNCTYPE(

            None,

            ctypes.c_void_p,

            ctypes.c_void_p,

            ctypes.c_void_p

        )(

            vtable[47]

        )





        CopyResource(

            self.context,

            destination,

            source

        )



        print(
            "CopyResource ejecutado"
        )


        return True