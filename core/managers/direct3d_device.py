import ctypes


class Direct3DDeviceManager:


    def __init__(self):

        self.device = None



    # =====================================
    # Crear dispositivo D3D11
    # =====================================

    def create_device(self):

        print(
            "Creando dispositivo Direct3D11"
        )


        try:

            # Cargamos d3d11.dll

            d3d11 = ctypes.windll.d3d11


            # Aquí dejaremos el handle nativo

            device = ctypes.c_void_p()



            # Flags básicos

            D3D_DRIVER_TYPE_HARDWARE = 1


            D3D11_CREATE_DEVICE_BGRA_SUPPORT = 0x20



            feature_level = ctypes.c_uint()



            # Crear dispositivo

            result = (
                d3d11.D3D11CreateDevice(
                    None,
                    D3D_DRIVER_TYPE_HARDWARE,
                    None,
                    D3D11_CREATE_DEVICE_BGRA_SUPPORT,
                    None,
                    0,
                    7,
                    ctypes.byref(device),
                    ctypes.byref(feature_level),
                    None
                )
            )



            if result != 0:

                print(
                    "Error D3D11CreateDevice:",
                    hex(result)
                )

                return False



            self.device = device



            print(
                "Dispositivo D3D11 creado"
            )


            return True



        except Exception as e:


            print(
                "Error creando D3D11:"
            )


            print(
                e
            )


            return False



    # =====================================
    # Obtener dispositivo
    # =====================================

    def get_device(self):

        return self.device