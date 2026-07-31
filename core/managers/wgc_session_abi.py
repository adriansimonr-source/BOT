import ctypes





class WGCSessionABI:


    def __init__(self):

        self.session = None







    # ==================================================
    # Crear GraphicsCaptureSession
    # ==================================================


    def create_session(

        self,

        framepool,

        item

    ):


        print(
            "Creando GraphicsCaptureSession"
        )



        obj = ctypes.cast(

            framepool,

            ctypes.POINTER(

                ctypes.POINTER(

                    ctypes.c_void_p

                )

            )

        )


        vtable = obj.contents





        CreateCaptureSession = ctypes.CFUNCTYPE(

            ctypes.c_long,

            ctypes.c_void_p,

            ctypes.c_void_p,

            ctypes.POINTER(

                ctypes.c_void_p

            )

        )(

            vtable[10]

        )





        session = ctypes.c_void_p()



        hr = CreateCaptureSession(

            framepool,

            item,

            ctypes.byref(

                session

            )

        )



        print(

            "CreateCaptureSession HRESULT:",

            hex(

                hr & 0xffffffff

            )

        )



        if hr != 0:

            raise OSError(

                hr,

                "CreateCaptureSession fallo"

            )





        self.session = session



        print(

            "SESSION:",

            session

        )



        return session







    # ==================================================
    # Debug session
    # ==================================================


    def debug_session(self):


        if self.session is None:

            return



        obj = ctypes.cast(

            self.session,

            ctypes.POINTER(

                ctypes.POINTER(

                    ctypes.c_void_p

                )

            )

        )


        vtable = obj.contents



        print(

            "VTABLE SESSION"

        )



        for i in range(10):


            print(

                i,

                hex(

                    ctypes.cast(

                        vtable[i],

                        ctypes.c_void_p

                    ).value

                )

            )









    # ==================================================
    # StartCapture
    # ==================================================


    def start_capture(

        self

    ):


        if self.session is None:

            raise RuntimeError(

                "No existe session"

            )





        self.debug_session()





        obj = ctypes.cast(

            self.session,

            ctypes.POINTER(

                ctypes.POINTER(

                    ctypes.c_void_p

                )

            )

        )


        vtable = obj.contents





        #
        # IGraphicsCaptureSession
        #
        # 0 QueryInterface
        # 1 AddRef
        # 2 Release
        # 3 GetIids
        # 4 GetRuntimeClassName
        # 5 GetTrustLevel
        # 6 StartCapture
        #



        StartCapture = ctypes.CFUNCTYPE(

            ctypes.c_long,

            ctypes.c_void_p

        )(

            vtable[6]

        )





        print(

            "Ejecutando StartCapture"

        )



        hr = StartCapture(

            self.session

        )





        print(

            "StartCapture HRESULT:",

            hex(

                hr & 0xffffffff

            )

        )





        if hr != 0:

            raise OSError(

                hr,

                "StartCapture fallo"

            )





        print(

            "CAPTURA INICIADA"

        )