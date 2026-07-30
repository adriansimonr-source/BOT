import time
import ctypes
import comtypes


from core.managers.window_manager import WindowManager
from core.managers.direct3d_device import Direct3DDeviceManager
from core.managers.direct3d_converter import Direct3DConverter

from core.managers.wgc_framepool_abi import WGCFramePoolABI
from core.managers.wgc_item_abi import WGCItemABI
from core.managers.wgc_session_abi import WGCSessionABI
from core.managers.wgc_frame_reader_abi import WGCFrameReaderABI
from core.managers.wgc_frame_abi import WGCFrameABI



WINDOW_TITLE = (
    "Kathana - The Reign of Shadow"
)


WIDTH = 1920
HEIGHT = 1080



# ==================================================
# GUID DXGI ACCESS
# ==================================================

IID_DXGI_ACCESS = comtypes.GUID(
    "{A9B3D012-3DF2-4EE3-B8D1-8695F457D3C1}"
)





# ==================================================
# QueryInterface Surface
# ==================================================

def query_dxgi_access(surface):


    print(
        "Consultando IDirect3DDxgiInterfaceAccess"
    )



    obj = ctypes.cast(

        surface,

        ctypes.POINTER(

            ctypes.POINTER(
                ctypes.c_void_p
            )

        )

    )


    vtable = obj.contents



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

        vtable[0]

    )



    access = ctypes.c_void_p()



    hr = QueryInterface(

        surface,

        ctypes.byref(
            IID_DXGI_ACCESS
        ),

        ctypes.byref(
            access
        )

    )



    print(

        "QI DXGI HRESULT:",

        hex(
            hr & 0xffffffff
        )

    )


    print(
        "DXGI ACCESS:",
        access
    )


    return access





# ==================================================
# CAPTURE
# ==================================================

window = WindowManager()


if not window.find_window_by_title(
    WINDOW_TITLE
):

    raise Exception(
        "Ventana no encontrada"
    )



hwnd = window.hwnd



print(
    "HWND:",
    hwnd
)





# D3D11

d3d = Direct3DDeviceManager()


if not d3d.create_device():

    raise Exception(
        "Error D3D11"
    )



converter = Direct3DConverter()



if not converter.create_winrt_device(

    d3d.get_device()

):

    raise Exception(
        "Error WinRT Device"
    )



device = converter.get_device()





# FramePool

framepool_abi = WGCFramePoolABI()


framepool_abi.get_statics2()



framepool = framepool_abi.create_free_threaded(

    device,

    WIDTH,

    HEIGHT

)





# Item

item = WGCItemABI().create_for_window(

    hwnd

)





# Session

session = WGCSessionABI()



session.create_session(

    framepool,

    item

)



session.start_capture()



print(
    "CAPTURA INICIADA"
)



time.sleep(2)





# Reader

reader = WGCFrameReaderABI()


reader.set_framepool(

    framepool

)



frame_reader = WGCFrameABI()





print(
    "ESPERANDO FRAME"
)





while True:


    frame = reader.try_get_next_frame()



    if frame is None:

        time.sleep(
            0.05
        )

        continue



    print()

    print(
        "FRAME:",
        frame
    )



    frame_reader.set_frame(

        frame

    )



    surface = frame_reader.get_surface()



    print(
        "SURFACE:",
        surface
    )



    access = query_dxgi_access(

        surface

    )



    print()

    print(
        "RESULTADO:"
    )


    if access:

        print(
            "DXGI ACCESS CONSEGUIDO"
        )

    else:

        print(
            "NO HAY DXGI ACCESS"
        )



    break





reader.release_frame(

    frame

)