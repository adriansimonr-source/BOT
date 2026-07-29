import ctypes
import comtypes

import winrt.windows.graphics.directx.direct3d11 as d3d11



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
    # Crear IDirect3DDevice WinRT
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

            d3d11 = ctypes.windll.LoadLibrary(
                "d3d11.dll"
            )



            CreateDirect3D11DeviceFromDXGIDevice = (
                d3d11
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



            winrt_device_ptr = ctypes.c_void_p()



            hr = (
                CreateDirect3D11DeviceFromDXGIDevice(
                    dxgi_device,
                    ctypes.byref(
                        winrt_device_ptr
                    )
                )
            )



            if hr != 0:

                print(
                    "Error creando WinRT Device:",
                    hex(hr)
                )

                return False



            print(
                "IDirect3DDevice COM creado"
            )



            # ---------------------------------
            # Convertir COM -> objeto WinRT
            # ---------------------------------

            self.winrt_device = (
                d3d11.IDirect3DDevice._from(
                    winrt_device_ptr
                )
            )



            print(
                "IDirect3DDevice WinRT convertido"
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



    # =====================================
    # Obtener dispositivo
    # =====================================

    def get_device(
        self
    ):

        return self.winrt_device