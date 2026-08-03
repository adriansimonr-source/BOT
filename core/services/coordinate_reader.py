import cv2
import os
import re
import pytesseract

from collections import Counter




class CoordinateReader:


    def __init__(self):


        # última coordenada válida

        self.last_value = None


        # indica si ya aceptamos
        # la primera posición de esta sesión

        self.initialized = False



        self.debug = True



        os.makedirs(
            "debug_coordinates",
            exist_ok=True
        )







    # =====================================
    # RESET SESION
    # =====================================


    def reset(self):


        self.last_value = None

        self.initialized = False



        print(
            "[CoordinateReader] reset"
        )









    # =====================================
    # LIMPIEZA OCR
    # =====================================


    def clean_text(
        self,
        text
    ):


        original = text



        text = (

            text

            .replace("\n", "")

            .replace(" ", "")

            .replace("/", "")

            .replace("|", "")

            .replace("O", "0")

            .replace("I", "1")

            .replace("l", "1")

        )



        numbers = re.findall(

            r"\d+",

            text

        )



        if not numbers:


            print(

                "[OCR VACIO]",

                repr(original)

            )


            return None





        value = numbers[0]



        # máximo 3 cifras

        if len(value) > 3:

            value = value[-3:]



        return value







    # =====================================
    # OCR MULTIPLE
    # =====================================


    def read_number(

        self,

        image,

        name

    ):



        if self.debug:


            cv2.imwrite(

                f"debug_coordinates/{name}_original.png",

                image

            )




        gray = cv2.cvtColor(

            image,

            cv2.COLOR_BGR2GRAY

        )




        if self.debug:


            cv2.imwrite(

                f"debug_coordinates/{name}_gray.png",

                gray

            )






        configs = [


            "--psm 7 -c tessedit_char_whitelist=0123456789",


            "--psm 8 -c tessedit_char_whitelist=0123456789",


            "--psm 13 -c tessedit_char_whitelist=0123456789"


        ]




        results = []





        for config in configs:



            text = pytesseract.image_to_string(

                gray,

                config=config

            )




            value = self.clean_text(

                text

            )





            print(

                "[TRY OCR]",

                name,

                config,

                repr(text),

                "=>",

                value

            )




            if value is not None:


                results.append(

                    int(value)

                )








        if not results:



            print(

                "[OCR FINAL]",

                name,

                None

            )


            return None







        counter = Counter(

            results

        )



        value = counter.most_common(1)[0][0]





        print(

            "[OCR FINAL]",

            name,

            value,

            "votos:",

            counter

        )




        return str(value)









    # =====================================
    # VALIDACION
    # =====================================


    def validate(

        self,

        coord

    ):



        # Primera lectura tras arrancar

        if not self.initialized:



            self.last_value = coord


            self.initialized = True



            print(

                "[POSITION INITIALIZED]",

                coord

            )



            return coord







        dx = abs(

            coord["x"]

            -

            self.last_value["x"]

        )



        dy = abs(

            coord["y"]

            -

            self.last_value["y"]

        )






        # salto demasiado grande

        if dx > 20 or dy > 20:



            print(

                "[DESCARTADO]",

                coord,

                "anterior:",

                self.last_value

            )



            return self.last_value







        self.last_value = coord



        return coord











    # =====================================
    # READ
    # =====================================


    def read(

        self,

        image

    ):



        print(

            "[CoordinateReader]",

            image.shape

        )





        if self.debug:


            cv2.imwrite(

                "debug_coordinates/full_coordinate.png",

                image

            )







        # =================================
        # CROPS CALIBRADOS
        # =================================


        x_crop = image[

            0:18,

            0:40

        ]




        y_crop = image[

            0:18,

            45:80

        ]






        if self.debug:



            cv2.imwrite(

                "debug_coordinates/x_crop.png",

                x_crop

            )



            cv2.imwrite(

                "debug_coordinates/y_crop.png",

                y_crop

            )







        x = self.read_number(

            x_crop,

            "x"

        )




        y = self.read_number(

            y_crop,

            "y"

        )







        print(

            "[RAW RESULT]",

            x,

            y

        )







        if x is None or y is None:


            return self.last_value







        coord = {


            "x": int(x),


            "y": int(y)


        }






        return self.validate(

            coord

        )