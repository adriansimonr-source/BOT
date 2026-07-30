import time


from core.managers.window_manager import WindowManager
from core.managers.direct3d_device import Direct3DDeviceManager
from core.managers.direct3d_converter import Direct3DConverter
from core.managers.direct3d_context import Direct3DContextManager
from core.managers.direct3d_staging import Direct3DStagingManager
from core.managers.direct3d_copy import Direct3DCopyManager
from core.managers.direct3d_map import Direct3DMapManager
from core.managers.direct3d_texture import D3D11TextureManager

from core.managers.wgc_framepool_abi import WGCFramePoolABI
from core.managers.wgc_item_abi import WGCItemABI
from core.managers.wgc_session_abi import WGCSessionABI
from core.managers.wgc_frame_reader_abi import WGCFrameReaderABI
from core.managers.wgc_frame_abi import WGCFrameABI
from core.managers.wgc_surface_abi import WGCSurfaceABI



TITLE = "Kathana - The Reign of Shadow"
WIDTH = 1920
HEIGHT = 1080



def ok(msg):
    print("\n[OK]", msg)



# ----------------------------
# Window
# ----------------------------

window = WindowManager()

if not window.find_window_by_title(TITLE):
    raise Exception("Ventana no encontrada")


hwnd = window.hwnd

ok(f"HWND {hwnd}")



# ----------------------------
# DirectX Device
# ----------------------------

d3d = Direct3DDeviceManager()

if not d3d.create_device():
    raise Exception("D3D11 fallo")


device = d3d.get_device()


context = Direct3DContextManager().create_context(
    device
)


ok("Device + Context")



# ----------------------------
# WinRT Device
# ----------------------------

converter = Direct3DConverter()

if not converter.create_winrt_device(device):
    raise Exception("WinRT fallo")


winrt_device = converter.get_device()


ok("WinRT Device")



# ----------------------------
# WGC Capture
# ----------------------------

pool = WGCFramePoolABI()

pool.get_statics2()

framepool = pool.create_free_threaded(
    winrt_device,
    WIDTH,
    HEIGHT
)



item = WGCItemABI().create_for_window(hwnd)


session = WGCSessionABI()

session.create_session(
    framepool,
    item
)

session.start_capture()


time.sleep(2)


ok("Capture iniciado")



# ----------------------------
# Managers
# ----------------------------

reader = WGCFrameReaderABI()
reader.set_framepool(framepool)


frame_mgr = WGCFrameABI()

surface_mgr = WGCSurfaceABI()


texture_mgr = D3D11TextureManager()


staging_mgr = Direct3DStagingManager()
staging_mgr.set_device(
    device,
    context
)


copy_mgr = Direct3DCopyManager()
copy_mgr.set_context(context)


map_mgr = Direct3DMapManager()
map_mgr.set_context(context)



# ----------------------------
# Capture Frame
# ----------------------------


print("\nEsperando frame...")


while True:

    frame = reader.try_get_next_frame()

    if frame is None:
        time.sleep(0.05)
        continue


    try:

        ok("Frame recibido")


        frame_mgr.set_frame(frame)


        surface = frame_mgr.get_surface()

        ok("Surface")



        access = surface_mgr.get_dxgi_access(surface)


        texture = surface_mgr.get_texture(access)


        ok("Texture obtenida")



        texture_mgr.set_texture(texture)

        texture_mgr.get_desc()



        # GPU -> CPU texture

        staging = staging_mgr.create_staging(texture)


        ok("Staging creada")



        copy_mgr.copy_resource(
            staging,
            texture
        )


        ok("CopyResource")



        # Leer memoria

        mapped = map_mgr.map_texture(
            staging
        )


        ok("MAP correcto")


        print(
            "\nRESULTADO FINAL"
        )

        print(
            "Puntero:",
            mapped.pData
        )

        print(
            "RowPitch:",
            mapped.RowPitch
        )

        print(
            "DepthPitch:",
            mapped.DepthPitch
        )



        map_mgr.unmap_texture(
            staging
        )


        ok("UNMAP")


        break



    finally:

        reader.release_frame(frame)



print(
    "\n=============================="
)

print(
    "PIPELINE GPU -> CPU COMPLETADO"
)

print(
    "=============================="
)