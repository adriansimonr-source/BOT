import numpy as np





class BarReader:



    def __init__(self):


        # =====================================
        # Anchos calibrados Kathana
        # =====================================


        self.full_widths = {


            "player_hp": 245,


            "player_mp": 244,


            "enemy_hp": 233


        }





        # =====================================
        # Umbrales color
        # =====================================


        self.colors = {


            "red": {


                "r": 130,

                "g": 120,

                "b": 120

            },


            "blue": {


                "b": 100,

                "r": 170,

                "g": 170

            }


        }







    # =====================================
    # PUBLIC API
    # =====================================


    def read_hp(self, image):


        return self.read_bar(

            image,

            "red",

            "player_hp"

        )






    def read_mp(self, image):


        return self.read_bar(

            image,

            "blue",

            "player_mp"

        )







    def read_enemy_hp(self, image):


        return self.read_bar(

            image,

            "red",

            "enemy_hp"

        )









    # =====================================
    # CORE
    # =====================================


    def read_bar(

        self,

        image,

        color,

        bar_type

    ):


        if image is None:

            return 0





        if image.size == 0:

            return 0





        mask = self.create_mask(

            image,

            color

        )



        if not np.any(mask):

            return 0







        # Número de píxeles verticales
        # necesarios para considerar
        # una columna activa


        min_pixels = max(

            1,

            int(

                image.shape[0] * 0.30

            )

        )





        column_pixels = np.sum(

            mask,

            axis=0

        )





        active_columns = np.where(

            column_pixels >= min_pixels

        )[0]





        detected_width = len(

            active_columns

        )



        if detected_width <= 0:

            return 0





        full_width = self.full_widths.get(

            bar_type,

            detected_width

        )





        percentage = (

            detected_width /

            full_width

        ) * 100





        # Normalización Kathana

        if percentage >= 96:

            percentage = 100





        percentage = max(

            0,

            min(

                100,

                percentage

            )

        )





        return round(

            percentage,

            2

        )









    # =====================================
    # MASK
    # =====================================


    def create_mask(

        self,

        image,

        color

    ):


        # OpenCV BGR

        b = image[:, :, 0]

        g = image[:, :, 1]

        r = image[:, :, 2]





        if color == "red":


            threshold = self.colors["red"]



            return (

                (r > threshold["r"])

                &

                (g < threshold["g"])

                &

                (b < threshold["b"])

            )







        if color == "blue":


            threshold = self.colors["blue"]



            return (

                (b > threshold["b"])

                &

                (r < threshold["r"])

                &

                (g < threshold["g"])

            )







        return np.zeros(

            image.shape[:2],

            dtype=bool

        )