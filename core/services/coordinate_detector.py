import cv2
import os
import numpy as np



class CoordinateDetector:


    def __init__(self):

        self.templates_x = {}
        self.templates_y = {}



    # ==============================
    # CARGAR PLANTILLAS
    # ==============================

    def load_template_x(
        self,
        value,
        path
    ):

        image = cv2.imread(
            path,
            cv2.IMREAD_COLOR
        )


        if image is None:

            raise Exception(
                f"No existe plantilla {path}"
            )


        self.templates_x[value] = image




    def load_template_y(
        self,
        value,
        path
    ):

        image = cv2.imread(
            path,
            cv2.IMREAD_COLOR
        )


        if image is None:

            raise Exception(
                f"No existe plantilla {path}"
            )


        self.templates_y[value] = image




    # ==============================
    # MATCH
    # ==============================

    def match(
        self,
        image,
        templates
    ):


        best = None

        best_score = 0



        for value, template in templates.items():


            result = cv2.matchTemplate(

                image,

                template,

                cv2.TM_CCOEFF_NORMED

            )


            score = float(
                result.max()
            )



            if score > best_score:

                best_score = score

                best = value



        if best is None:

            return None



        return {

            "value": best,

            "confidence": best_score

        }



    # ==============================
    # DETECTAR COORDENADA
    # ==============================

    def detect(
        self,
        coordinate_box
    ):


        x_image = coordinate_box[
            0:18,
            0:40
        ]


        y_image = coordinate_box[
            0:18,
            45:80
        ]



        x = self.match(
            x_image,
            self.templates_x
        )


        y = self.match(
            y_image,
            self.templates_y
        )



        if x is None or y is None:

            return None



        return {

            "x": int(x["value"]),

            "y": int(y["value"]),

            "confidence_x": x["confidence"],

            "confidence_y": y["confidence"]

        }