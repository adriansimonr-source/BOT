import ctypes

from core.managers.com_utils import get_vtable


class D3D11Texture2DDescription(ctypes.Structure):
    _fields_ = [
        ("Width", ctypes.c_uint32),
        ("Height", ctypes.c_uint32),
        ("MipLevels", ctypes.c_uint32),
        ("ArraySize", ctypes.c_uint32),
        ("Format", ctypes.c_uint32),
        ("SampleDescCount", ctypes.c_uint32),
        ("SampleDescQuality", ctypes.c_uint32),
        ("Usage", ctypes.c_uint32),
        ("BindFlags", ctypes.c_uint32),
        ("CPUAccessFlags", ctypes.c_uint32),
        ("MiscFlags", ctypes.c_uint32),
    ]


class Direct3DStagingManager:

    D3D11_USAGE_STAGING = 3
    D3D11_CPU_ACCESS_READ = 0x20000

    def __init__(self):
        self.device = None
        self.context = None
        self.staging = None

    def set_device(self, device, context):
        self.device = device
        self.context = context

    def create_staging(self, source_texture):
        get_description = ctypes.WINFUNCTYPE(
            None,
            ctypes.c_void_p,
            ctypes.POINTER(D3D11Texture2DDescription),
        )(get_vtable(source_texture)[10])
        description = D3D11Texture2DDescription()
        get_description(source_texture, ctypes.byref(description))
        description.Usage = self.D3D11_USAGE_STAGING
        description.BindFlags = 0
        description.CPUAccessFlags = self.D3D11_CPU_ACCESS_READ
        description.MiscFlags = 0

        create_texture = ctypes.WINFUNCTYPE(
            ctypes.c_long,
            ctypes.c_void_p,
            ctypes.POINTER(D3D11Texture2DDescription),
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p),
        )(get_vtable(self.device)[5])
        staging = ctypes.c_void_p()
        hr = create_texture(
            self.device,
            ctypes.byref(description),
            None,
            ctypes.byref(staging),
        )
        if hr != 0:
            raise OSError(hr, "No se pudo crear staging")
        self.staging = staging
        return staging
