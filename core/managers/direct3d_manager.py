import winrt.windows.graphics.directx as directx
import winrt.windows.graphics.directx.direct3d11 as direct3d11


class Direct3DManager:


    def __init__(self):

        self.device = None



    # =====================================
    # Crear dispositivo D3D11
    # =====================================

    def create_device(self):

        print(
            "Creando dispositivo Direct3D11"
        )


        # Aquí crearemos:
        #
        # ID3D11Device nativo
        # |
        # v
        # IDirect3DDevice WinRT


        return None



    # =====================================
    # Obtener dispositivo
    # =====================================

    def get_device(self):

        return self.device