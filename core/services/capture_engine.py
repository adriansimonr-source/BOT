import time


from core.managers.window_manager import WindowManager

from core.managers.direct3d_device import Direct3DDeviceManager
from core.managers.direct3d_context import Direct3DContextManager
from core.managers.direct3d_converter import Direct3DConverter

from core.managers.wgc_framepool_abi import WGCFramePoolABI
from core.managers.wgc_item_abi import WGCItemABI
from core.managers.wgc_session_abi import WGCSessionABI
from core.managers.wgc_frame_reader_abi import WGCFrameReaderABI

from core.managers.wgc_frame_abi import WGCFrameABI
from core.managers.wgc_surface_abi import WGCSurfaceABI

from core.managers.direct3d_staging import Direct3DStagingManager
from core.managers.direct3d_copy import Direct3DCopyManager
from core.managers.direct3d_map import Direct3DMapManager

from core.managers.frame_cpu_reader import FrameCPUReader


from core.models.frame import Frame






class CaptureEngine:


    def __init__(

        self,

        title,

        width,

        height

    ):


        self.title = title

        self.width = width

        self.height = height



        self.running = False



        self.reader = None



        #
        # Staging persistente
        #

        self.staging_texture = None






    # ==========================================
    # START
    # ==========================================


    def start(self):


        if self.running:

            return





        # ==============================
        # WINDOW
        # ==============================


        window = WindowManager()



        if not window.find_window_by_title(

            self.title

        ):

            raise Exception(

                "Ventana no encontrada"

            )



        hwnd = window.hwnd






        # ==============================
        # D3D DEVICE
        # ==============================


        d3d = Direct3DDeviceManager()



        if not d3d.create_device():

            raise Exception(

                "Error creando D3D11"

            )



        device = d3d.get_device()






        # ==============================
        # DEVICE CONTEXT
        # ==============================


        context_manager = Direct3DContextManager()



        context = context_manager.create_context(

            device

        )







        # ==============================
        # WINRT DEVICE
        # ==============================


        converter = Direct3DConverter()



        if not converter.create_winrt_device(

            device

        ):

            raise Exception(

                "Error creando WinRT Device"

            )



        winrt = converter.get_device()







        # ==============================
        # FRAMEPOOL
        # ==============================


        pool = WGCFramePoolABI()



        pool.get_statics2()



        framepool = pool.create_free_threaded(

            winrt,

            self.width,

            self.height

        )







        # ==============================
        # CAPTURE ITEM
        # ==============================


        item = WGCItemABI().create_for_window(

            hwnd

        )







        # ==============================
        # SESSION
        # ==============================


        session = WGCSessionABI()



        session.create_session(

            framepool,

            item

        )



        session.start_capture()



        time.sleep(1)







        # ==============================
        # FRAME READER
        # ==============================


        self.reader = WGCFrameReaderABI()



        self.reader.set_framepool(

            framepool

        )







        # ==============================
        # GPU PIPELINE
        # ==============================


        self.frame_manager = WGCFrameABI()



        self.surface_manager = WGCSurfaceABI()






        self.staging = Direct3DStagingManager()



        self.staging.set_device(

            device,

            context

        )







        self.copy = Direct3DCopyManager()



        self.copy.set_context(

            context

        )







        self.map = Direct3DMapManager()



        self.map.set_context(

            context

        )







        self.cpu = FrameCPUReader()



        self.cpu.set_size(

            self.width,

            self.height

        )







        # Referencias

        self.device = device

        self.context = context

        self.framepool = framepool

        self.item = item

        self.session = session







        self.running = True



        print(

            "[CaptureEngine] iniciado"

        )









    # ==========================================
    # GET FRAME
    # ==========================================


    def get_frame(self):


        if not self.running:

            raise RuntimeError(

                "CaptureEngine no iniciado"

            )







        frame = None





        while frame is None:


            frame = self.reader.try_get_next_frame()



            if frame is None:


                time.sleep(

                    0.005

                )







        try:



            # ==============================
            # FRAME -> SURFACE
            # ==============================


            self.frame_manager.set_frame(

                frame

            )



            surface = self.frame_manager.get_surface()






            # ==============================
            # SURFACE -> TEXTURE
            # ==============================


            access = self.surface_manager.get_dxgi_access(

                surface

            )



            texture = self.surface_manager.get_texture(

                access

            )







            # ==============================
            # STAGING UNA SOLA VEZ
            # ==============================


            if self.staging_texture is None:



                self.staging_texture = self.staging.create_staging(

                    texture

                )



                print(

                    "[CaptureEngine] staging creado"

                )








            # ==============================
            # GPU -> CPU
            # ==============================


            self.copy.copy_resource(

                self.staging_texture,

                texture

            )







            mapped = self.map.map_texture(

                self.staging_texture

            )







            image = self.cpu.read_frame(

                mapped

            )







            self.map.unmap_texture(

                self.staging_texture

            )







            return Frame(

                image,

                time.time()

            )







        finally:



            self.reader.release_frame(

                frame

            )









    # ==========================================
    # STOP
    # ==========================================


    def stop(self):


        if not self.running:

            return






        self.running = False



        self.reader = None

        self.framepool = None

        self.item = None

        self.session = None



        self.staging_texture = None





        print(

            "[CaptureEngine] detenido"

        )