import cv2
import os





class NameDetector:


    def __init__(

        self,

        threshold=0.85

    ):


        self.threshold = threshold


        self.enemy_templates = {}

        self.player_templates = {}






    # =====================================
    # CARGAR TEMPLATES
    # =====================================


    def load_enemy_templates(

        self,

        folder

    ):


        self.enemy_templates = self.load_folder(

            folder

        )





    def load_player_templates(

        self,

        folder

    ):


        self.player_templates = self.load_folder(

            folder

        )







    def load_folder(

        self,

        folder

    ):


        templates = {}



        if not os.path.exists(folder):

            return templates





        for file in os.listdir(folder):


            if not file.endswith(".png"):

                continue



            path = os.path.join(

                folder,

                file

            )



            image = cv2.imread(

                path,

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
    # DETECTAR NOMBRE
    # =====================================


    def detect_enemy(

        self,

        image

    ):


        return self.detect(

            image,

            self.enemy_templates

        )






    def detect_player(

        self,

        image

    ):


        return self.detect(

            image,

            self.player_templates

        )







    def detect(

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


            result = cv2.matchTemplate(

                gray,

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