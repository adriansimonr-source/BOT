import time


from core.managers.window_manager import WindowManager

from core.managers.direct3d_device import (
    Direct3DDeviceManager
)

from core.managers.direct3d_converter import (
    Direct3DConverter
)

from core.managers.wgc_framepool_abi import (
    WGCFramePoolABI
)

from core.managers.wgc_item_abi import (
    WGCItemABI
)

from core.managers.wgc_session_abi import (
    WGCSessionABI
)

from core.managers.wgc_frame_reader_abi import (
    WGCFrameReaderABI
)



# ==================================================
# WINDOW
# ==================================================

window = WindowManager()


if not window.find_window_by_title(
    "Kathana - The Reign of Shadow"
):

    raise Exception(
        "Kathana no encontrada"
    )


hwnd = window.hwnd


print(
    "HWND:",
    hwnd
)



# ==================================================
# D3D11 DEVICE
# ==================================================

d3d_manager = Direct3DDeviceManager()


if not d3d_manager.create_device():

    raise Exception(
        "Error creando D3D11"
    )


d3d_device = d3d_manager.get_device()



# ==================================================
# WINRT DEVICE
# ==================================================

converter = Direct3DConverter()


if not converter.create_winrt_device(
    d3d_device
):

    raise Exception(
        "Error convirtiendo device"
    )


winrt_device = converter.get_device()



print(
    "DEVICE WINRT:"
)

print(
    winrt_device
)



# ==================================================
# FRAMEPOOL
# ==================================================

framepool_abi = WGCFramePoolABI()


print(
    "Inicializando STATICS2"
)


framepool_abi.get_statics2()



framepool = framepool_abi.create_free_threaded(

    winrt_device,

    1920,

    1080

)



print(
    "FRAMEPOOL:"
)

print(
    framepool
)



# ==================================================
# ITEM
# ==================================================

item_abi = WGCItemABI()


item = item_abi.create_for_window(

    hwnd

)



print(
    "ITEM:"
)

print(
    item
)



# ==================================================
# SESSION
# ==================================================

session_abi = WGCSessionABI()


session = session_abi.create_session(

    framepool,

    item

)



print(
    "SESSION:"
)

print(
    session
)



session_abi.start_capture()



print(
    "CAPTURA FUNCIONANDO"
)



# ==================================================
# FRAME READER
# ==================================================

reader = WGCFrameReaderABI()


reader.set_framepool(

    framepool

)



print(
    "Esperando frames..."
)



while True:


    frame = reader.try_get_frame()



    if frame:

        print(
            "FRAME RECIBIDO:",
            frame
        )



    time.sleep(
        0.01
    )