import cv2
import pytesseract
import numpy as np





class OCRReader:


    def __init__(self):


        self.text_config = (

            "--psm 7"

        )


        self.number_config = (

            "--psm 7 "

            "-c tessedit_char_whitelist=0123456789"

        )







    # =====================================
    # TEXTO GENERAL
    # =====================================


    def read_text(

        self,

        image

    ):


        processed = self.preprocess(

            image

        )


        if processed is None:

            return ""




        text = pytesseract.image_to_string(

            processed,

            config=self.text_config

        )



        return self.clean_text(

            text

        )









    # =====================================
    # NUMEROS
    # =====================================


    def read_number(

        self,

        image

    ):


        processed = self.preprocess(

            image,

            numbers=True

        )


        if processed is None:

            return 0





        text = pytesseract.image_to_string(

            processed,

            config=self.number_config

        )



        text = self.clean_text(

            text

        )



        try:

            return int(text)


        except:


            return 0







    # =====================================
    # PREPROCESADO
    # =====================================


    def preprocess(

        self,

        image,

        numbers=False

    ):


        if image is None:

            return None



        if image.size == 0:

            return None





        gray = cv2.cvtColor(

            image,

            cv2.COLOR_BGR2GRAY

        )





        # Aumentamos tamaño
        # Los textos del HUD son pequeños


        scale = 3


        gray = cv2.resize(

            gray,

            None,

            fx=scale,

            fy=scale,

            interpolation=cv2.INTER_CUBIC

        )






        # Umbral adaptativo


        _, threshold = cv2.threshold(

            gray,

            0,

            255,

            cv2.THRESH_BINARY +

            cv2.THRESH_OTSU

        )





        return threshold







    # =====================================
    # LIMPIEZA
    # =====================================


    def clean_text(

        self,

        text

    ):


        if not text:

            return ""



        text = text.strip()



        text = text.replace(

            "\n",

            " "

        )



        return text