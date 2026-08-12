import time

from core.managers.com_utils import close_winrt, release_com
from core.managers.direct3d_context import Direct3DContextManager
from core.managers.direct3d_converter import Direct3DConverter
from core.managers.direct3d_copy import Direct3DCopyManager
from core.managers.direct3d_device import Direct3DDeviceManager
from core.managers.direct3d_map import Direct3DMapManager
from core.managers.direct3d_staging import Direct3DStagingManager
from core.managers.frame_cpu_reader import FrameCPUReader
from core.managers.wgc_borderless import request_borderless_capture_access
from core.managers.wgc_frame_abi import WGCFrameABI
from core.managers.wgc_frame_reader_abi import WGCFrameReaderABI
from core.managers.wgc_framepool_abi import WGCFramePoolABI
from core.managers.wgc_item_abi import WGCItemABI
from core.managers.wgc_session_abi import WGCSessionABI
from core.managers.wgc_surface_abi import WGCSurfaceABI
from core.managers.window_manager import WindowManager
from core.models.frame import Frame


class CaptureEngine:

    FRAME_TIMEOUT_SECONDS = 0.01

    def __init__(self, title, width, height, hwnd=None):
        self.title = title
        self.width = int(width)
        self.height = int(height)
        self.hwnd = hwnd
        self.running = False
        self._clear_resource_references()

    def start(self):
        if self.running:
            return

        window = WindowManager()
        if self.hwnd:
            window.hwnd = self.hwnd
        if not window.is_valid() and not window.find_window_by_title(self.title):
            raise RuntimeError("Ventana no encontrada")

        borderless_allowed = request_borderless_capture_access()
        try:
            self.device_manager = Direct3DDeviceManager()
            if not self.device_manager.create_device():
                raise RuntimeError("Error creando D3D11")
            self.device = self.device_manager.get_device()

            self.context_manager = Direct3DContextManager()
            self.context = self.context_manager.create_context(self.device)
            self.converter = Direct3DConverter()
            if not self.converter.create_winrt_device(self.device):
                raise RuntimeError("Error creando WinRT Device")
            self.winrt_device = self.converter.get_device()

            self.pool_manager = WGCFramePoolABI()
            self.pool_manager.get_statics2()
            self.framepool = self.pool_manager.create_free_threaded(
                self.winrt_device,
                self.width,
                self.height,
            )
            self.item_manager = WGCItemABI()
            self.item = self.item_manager.create_for_window(window.hwnd)
            self.session_manager = WGCSessionABI()
            self.session = self.session_manager.create_session(
                self.framepool,
                self.item,
            )
            self.borderless_capture = (
                borderless_allowed
                and self.session_manager.try_disable_border()
            )
            self.session_manager.start_capture()

            self.reader = WGCFrameReaderABI()
            self.reader.set_framepool(self.framepool)
            self.frame_manager = WGCFrameABI()
            self.surface_manager = WGCSurfaceABI()
            self.staging = Direct3DStagingManager()
            self.staging.set_device(self.device, self.context)
            self.copy = Direct3DCopyManager()
            self.copy.set_context(self.context)
            self.map = Direct3DMapManager()
            self.map.set_context(self.context)
            self.cpu = FrameCPUReader()
            self.cpu.set_size(self.width, self.height)
            self.running = True
        except Exception:
            self._release_resources()
            raise

    def get_frame(self):
        if not self.running:
            raise RuntimeError("CaptureEngine no iniciado")

        frame = None
        deadline = time.perf_counter() + self.FRAME_TIMEOUT_SECONDS
        while frame is None:
            frame = self.reader.try_get_next_frame()
            if frame is None:
                if time.perf_counter() >= deadline:
                    return None
                time.sleep(0.005)

        surface = None
        access = None
        texture = None
        mapped = False
        try:
            self.frame_manager.set_frame(frame)
            surface = self.frame_manager.get_surface()
            access = self.surface_manager.get_dxgi_access(surface)
            texture = self.surface_manager.get_texture(access)
            if self.staging_texture is None:
                self.staging_texture = self.staging.create_staging(texture)

            self.copy.copy_resource(self.staging_texture, texture)
            mapped_resource = self.map.map_texture(self.staging_texture)
            mapped = True
            image = self.cpu.read_frame(mapped_resource)
            return Frame(image, time.time())
        finally:
            if mapped:
                self.map.unmap_texture(self.staging_texture)
            if texture:
                self.surface_manager.release_interface(texture)
            if access:
                self.surface_manager.release_interface(access)
            if surface:
                self.frame_manager.release_surface(surface)
            self.reader.release_frame(frame)

    def stop(self):
        self.running = False
        self._release_resources()

    def _release_resources(self):
        if self.reader:
            self.reader.set_framepool(None)

        self._safe_release(close_winrt, self.session)
        self._safe_release(close_winrt, self.framepool)
        self._safe_release(close_winrt, self.winrt_device)
        for interface in (
            self.session,
            self.framepool,
            self.item,
            self.staging_texture,
            getattr(self.pool_manager, "statics2", None),
            self.winrt_device,
            self.context,
            self.device,
        ):
            self._safe_release(release_com, interface)
        self._clear_resource_references()

    @staticmethod
    def _safe_release(operation, interface):
        if not interface:
            return
        try:
            operation(interface)
        except Exception:
            pass

    def _clear_resource_references(self):
        self.device_manager = None
        self.context_manager = None
        self.converter = None
        self.pool_manager = None
        self.item_manager = None
        self.session_manager = None
        self.device = None
        self.context = None
        self.winrt_device = None
        self.framepool = None
        self.item = None
        self.session = None
        self.reader = None
        self.frame_manager = None
        self.surface_manager = None
        self.staging = None
        self.staging_texture = None
        self.copy = None
        self.map = None
        self.cpu = None
        self.borderless_capture = False
