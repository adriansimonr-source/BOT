import ctypes


class Direct3DDeviceManager:

    D3D_DRIVER_TYPE_HARDWARE = 1
    D3D11_CREATE_DEVICE_BGRA_SUPPORT = 0x20

    def __init__(self):
        self.device = None

    def create_device(self):
        device = ctypes.c_void_p()
        feature_level = ctypes.c_uint()
        try:
            result = ctypes.windll.d3d11.D3D11CreateDevice(
                None,
                self.D3D_DRIVER_TYPE_HARDWARE,
                None,
                self.D3D11_CREATE_DEVICE_BGRA_SUPPORT,
                None,
                0,
                7,
                ctypes.byref(device),
                ctypes.byref(feature_level),
                None,
            )
        except OSError:
            return False
        if result != 0:
            return False
        self.device = device
        return True

    def get_device(self):
        return self.device
