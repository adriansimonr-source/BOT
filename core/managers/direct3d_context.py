import ctypes



class Direct3DContextManager:


    def __init__(self):

        self.context = None



    # ==========================================
    # Obtener Immediate Context
    # ==========================================

    def create_context(
        self,
        device
    ):


        print(
            "Obteniendo ID3D11DeviceContext"
        )



        obj = ctypes.cast(

            device,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        vtable = obj.contents



        print(
            "VTABLE DEVICE"
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



        #
        # ID3D11Device
        #
        # GetImmediateContext
        #
        # índice 40
        #



        GetImmediateContext = ctypes.WINFUNCTYPE(

            None,

            ctypes.c_void_p,

            ctypes.POINTER(
                ctypes.c_void_p
            )

        )(

            vtable[40]

        )



        context = ctypes.c_void_p()



        GetImmediateContext(

            device,

            ctypes.byref(
                context
            )

        )



        print(
            "CONTEXT:",
            context
        )


        self.context = context



        return context