import os
import cv2
import numpy as np





class NameMatcher:


    def __init__(

        self,

        threshold=0.85

    ):


        self.threshold = threshold


        self.enemy_templates = {}

        self.player_templates = {}






    # =====================================
    # LOAD
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


            if not file.endswith(".png"):

                continue





            image = cv2.imread(

                os.path.join(

                    path,

                    file

                ),

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
    # MATCH
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


            if gray.shape != template.shape:

                resized = cv2.resize(

                    gray,

                    (

                        template.shape[1],

                        template.shape[0]

                    )

                )

            else:

                resized = gray





            result = cv2.matchTemplate(

                resized,

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