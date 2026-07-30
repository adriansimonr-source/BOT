import time


from core.managers.window_manager import WindowManager
from core.managers.direct3d_device import Direct3DDeviceManager
from core.managers.direct3d_converter import Direct3DConverter

from core.managers.wgc_framepool_abi import WGCFramePoolABI
from core.managers.wgc_item_abi import WGCItemABI
from core.managers.wgc_session_abi import WGCSessionABI
from core.managers.wgc_frame_reader_abi import WGCFrameReaderABI
from core.managers.wgc_frame_abi import WGCFrameABI



WINDOW_TITLE = "Kathana - The Reign of Shadow"

WIDTH = 1920
HEIGHT = 1080



# =========================
# Window
# =========================

window = WindowManager()


if not window.find_window_by_title(WINDOW_TITLE):

    raise Exception(
        "Ventana no encontrada"
    )


hwnd = window.hwnd

print(
    "HWND:",
    hwnd
)



# =========================
# D3D11 -> WinRT Device
# =========================

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
        "Error convirtiendo D3D11"
    )


device = converter.get_device()


print(
    "WINRT DEVICE:",
    device
)



# =========================
# FramePool
# =========================

framepool_abi = WGCFramePoolABI()

framepool_abi.get_statics2()


framepool = framepool_abi.create_free_threaded(
    device,
    WIDTH,
    HEIGHT
)


print(
    "FRAMEPOOL:",
    framepool
)



# =========================
# Item
# =========================

item = WGCItemABI().create_for_window(
    hwnd
)


print(
    "ITEM:",
    item
)



# =========================
# Session
# =========================

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



# =========================
# Frame Reader
# =========================

reader = WGCFrameReaderABI()

reader.set_framepool(
    framepool
)


frame_abi = WGCFrameABI()



print(
    "LEYENDO FRAMES"
)



contador = 0



while True:


    frame = reader.try_get_next_frame()


    if frame is None:

        time.sleep(0.05)

        continue



    contador += 1


    print(
        "FRAME:",
        contador,
        frame
    )


    # =====================
    # Frame -> Surface
    # =====================

    try:

        frame_abi.set_frame(
            frame
        )


        surface = frame_abi.get_surface()


        print(
            "SURFACE:",
            surface
        )


        frame_abi.release_surface(
            surface
        )


    except Exception as e:


        print(
            "ERROR SURFACE:",
            e
        )



    reader.release_frame(
        frame
    )


    time.sleep(0.05)