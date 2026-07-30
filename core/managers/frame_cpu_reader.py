import ctypes
import numpy as np
import cv2



class FrameCPUReader:


    def __init__(self):

        self.width = 0
        self.height = 0




    # ==========================================
    # Configurar tamaño
    # ==========================================

    def set_size(

        self,

        width,

        height

    ):

        self.width = width
        self.height = height





    # ==========================================
    # Leer frame desde memoria CPU
    # ==========================================

    def read_frame(

        self,

        mapped

    ):


        if mapped is None:

            raise RuntimeError(
                "Mapped no disponible"
            )



        #
        # D3D11_MAPPED_SUBRESOURCE
        #
        # typedef struct {
        #
        #   void* pData;
        #   UINT RowPitch;
        #   UINT DepthPitch;
        #
        # }
        #


        pData = mapped.pData


        row_pitch = mapped.RowPitch



        size = row_pitch * self.height



        print(
            "Leyendo bytes:",
            size
        )



        #
        # Copiamos memoria GPU->CPU
        #

        buffer = ctypes.string_at(

            pData,

            size

        )




        #
        # Crear numpy
        #
        # IMPORTANTE:
        #
        # .copy()
        #
        # convierte la memoria
        # en editable para OpenCV
        #

        image = np.frombuffer(

            buffer,

            dtype=np.uint8

        ).copy()





        #
        # RowPitch puede ser mayor
        # que width*4
        #

        image = image.reshape(

            self.height,

            row_pitch

        )




        #
        # Recortar padding
        #

        image = image[:, :self.width * 4]




        #
        # BGRA
        #

        image = image.reshape(

            self.height,

            self.width,

            4

        )



        #
        # OpenCV trabaja mejor en BGR
        #
        # quitamos alpha
        #

        image = cv2.cvtColor(

            image,

            cv2.COLOR_BGRA2BGR

        )



        return image





    # ==========================================
    # Guardar PNG
    # ==========================================

    def save_png(

        self,

        image,

        filename

    ):


        cv2.imwrite(

            filename,

            image

        )


        print(

            "Imagen guardada:",

            filename

        )