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






class Direct3DStagingManager:


    def __init__(self):

        self.device = None
        self.context = None
        self.staging = None





    # ==================================================
    # Asignar D3D
    # ==================================================

    def set_device(

        self,

        device,

        context

    ):

        self.device = device

        self.context = context







    # ==================================================
    # Crear staging texture
    # ==================================================

    def create_staging(

        self,

        source_texture

    ):


        print(
            "Creando staging texture"
        )



        #
        # Obtener descripción original
        #


        texture_obj = ctypes.cast(

            source_texture,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        texture_vtable = texture_obj.contents



        GetDesc = ctypes.WINFUNCTYPE(

            None,

            ctypes.c_void_p,

            ctypes.POINTER(
                D3D11_TEXTURE2D_DESC
            )

        )(

            texture_vtable[10]

        )



        desc = D3D11_TEXTURE2D_DESC()



        GetDesc(

            source_texture,

            ctypes.byref(desc)

        )



        print(
            "SOURCE:",
            desc.Width,
            "x",
            desc.Height
        )





        #
        # Modificar para staging
        #


        D3D11_USAGE_STAGING = 3

        D3D11_CPU_ACCESS_READ = 0x20000



        desc.Usage = D3D11_USAGE_STAGING

        desc.BindFlags = 0

        desc.CPUAccessFlags = D3D11_CPU_ACCESS_READ

        desc.MiscFlags = 0






        #
        # Obtener CreateTexture2D
        #

        device_obj = ctypes.cast(

            self.device,

            ctypes.POINTER(

                ctypes.POINTER(
                    ctypes.c_void_p
                )

            )

        )


        device_vtable = device_obj.contents





        #
        # ID3D11Device
        #
        # CreateTexture2D = índice 5
        #


        CreateTexture2D = ctypes.WINFUNCTYPE(

            ctypes.c_long,

            ctypes.c_void_p,

            ctypes.POINTER(
                D3D11_TEXTURE2D_DESC
            ),

            ctypes.c_void_p,

            ctypes.POINTER(
                ctypes.c_void_p
            )

        )(

            device_vtable[5]

        )




        staging = ctypes.c_void_p()



        hr = CreateTexture2D(

            self.device,

            ctypes.byref(desc),

            None,

            ctypes.byref(staging)

        )



        print(
            "CreateTexture2D HRESULT:",
            hex(hr & 0xffffffff)
        )



        if hr != 0:

            raise OSError(
                hr,
                "No se pudo crear staging"
            )



        self.staging = staging



        print(
            "STAGING:",
            staging
        )



        return staging