import ctypes
import comtypes



# ==================================================
# GUID IDXGIDevice
# ==================================================

IDXGIDevice_GUID = comtypes.GUID(
    "{54EC77FA-1377-44E6-8C32-88FD5F44C84C}"
)



class Direct3DConverter:


    def __init__(self):

        self.winrt_device = None



    # =====================================
    # Crear WinRT IDirect3DDevice
    # =====================================

    def create_winrt_device(
        self,
        d3d_device
    ):


        print(
            "Convirtiendo D3D11 a WinRT Device"
        )


        try:


            dxgi_device = ctypes.c_void_p()



            # Obtener vtable COM

            vtable = ctypes.cast(
                d3d_device,
                ctypes.POINTER(
                    ctypes.POINTER(
                        ctypes.c_void_p
                    )
                )
            )



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
                vtable.contents[0]
            )



            hr = QueryInterface(
                d3d_device,
                ctypes.byref(
                    IDXGIDevice_GUID
                ),
                ctypes.byref(
                    dxgi_device
                )
            )



            if hr != 0:

                print(
                    "Error IDXGI:",
                    hex(hr)
                )

                return False



            print(
                "IDXGIDevice obtenido"
            )



            # ---------------------------------
            # Crear IDirect3DDevice WinRT
            # ---------------------------------


            d3d11_dll = ctypes.windll.LoadLibrary(
                "d3d11.dll"
            )



            CreateDirect3D11DeviceFromDXGIDevice = (
                d3d11_dll
                .CreateDirect3D11DeviceFromDXGIDevice
            )



            CreateDirect3D11DeviceFromDXGIDevice.argtypes = [

                ctypes.c_void_p,

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            ]



            CreateDirect3D11DeviceFromDXGIDevice.restype = (
                ctypes.HRESULT
            )



            winrt_device = ctypes.c_void_p()



            hr = (
                CreateDirect3D11DeviceFromDXGIDevice(
                    dxgi_device,
                    ctypes.byref(
                        winrt_device
                    )
                )
            )



            if hr != 0:

                print(
                    "Error creando WinRT Device:",
                    hex(hr)
                )

                return False



            self.winrt_device = winrt_device



            print(
                "IDirect3DDevice WinRT creado"
            )


            return True



        except Exception as e:


            print(
                "Error conversión:"
            )

            print(
                e
            )


            return False



    def get_device(self):

        return self.winrt_device