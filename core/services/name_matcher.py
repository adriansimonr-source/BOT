import os
import cv2
import numpy as np

from core.services.ocr_reader import OCRReader





class NameMatcher:


    def __init__(

        self,

        threshold=0.85

    ):


        self.threshold = threshold


        self.enemy_templates = {}

        self.player_templates = {}


        self.ocr = OCRReader()







    # =====================================
    # LOAD TEMPLATES
    # =====================================


    def load_enemy_templates(

        self,

        path

    ):


        self.enemy_templates = self.load_folder(

            path

        )





    def load_player_templates(

        self,

        path

    ):


        self.player_templates = self.load_folder(

            path

        )









    def load_folder(

        self,

        path

    ):


        templates = {}



        if not os.path.exists(path):

            return templates





        for file in os.listdir(path):


            if not file.lower().endswith(".png"):

                continue





            filepath = os.path.join(

                path,

                file

            )



            image = cv2.imread(

                filepath,

                cv2.IMREAD_GRAYSCALE

            )



            if image is None:

                continue





            name = os.path.splitext(

                file

            )[0]



            templates[name] = image





        return templates







    # =====================================
    # MATCH PUBLIC
    # =====================================


    def match_enemy(

        self,

        image

    ):


        return self.match(

            image,

            self.enemy_templates

        )







    def match_player(

        self,

        image

    ):


        return self.match(

            image,

            self.player_templates

        )









    # =====================================
    # OCR PUBLIC
    # =====================================


    def read_enemy_name(

        self,

        image

    ):


        # Primero intentamos template

        result = self.match_enemy(

            image

        )


        if result:

            return self.normalize(

                result

            )





        # Si no existe usamos OCR


        result = self.ocr.read_text(

            image

        )



        return self.normalize(

            result

        )









    def read_player_name(

        self,

        image

    ):


        result = self.match_player(

            image

        )


        if result:

            return self.normalize(

                result

            )





        result = self.ocr.read_text(

            image

        )



        return self.normalize(

            result

        )







    def read_number(

        self,

        image

    ):


        return self.ocr.read_number(

            image

        )









    # =====================================
    # CORE TEMPLATE MATCH
    # =====================================


    def match(

        self,

        image,

        templates

    ):


        if image is None:

            return None



        if not templates:

            return None





        gray = cv2.cvtColor(

            image,

            cv2.COLOR_BGR2GRAY

        )





        best_name = None

        best_score = 0





        for name, template in templates.items():



            current = gray





            if gray.shape != template.shape:


                current = cv2.resize(

                    gray,

                    (

                        template.shape[1],

                        template.shape[0]

                    )

                )





            result = cv2.matchTemplate(

                current,

                template,

                cv2.TM_CCOEFF_NORMED

            )





            score = result.max()





            if score > best_score:


                best_score = score

                best_name = name







        if best_score >= self.threshold:


            return best_name





        return None







    # =====================================
    # NORMALIZAR NOMBRE
    # =====================================


    def normalize(

        self,

        text

    ):


        if not text:

            return ""



        text = str(text)



        replacements = {

            "\n": " ",

            "_": " "

        }



        for old, new in replacements.items():

            text = text.replace(

                old,

                new

            )





        text = " ".join(

            text.split()

        )



        return text.strip()