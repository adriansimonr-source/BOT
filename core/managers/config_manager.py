import json
import os





class ConfigManager:


    def __init__(

        self,

        path="data/config.json"

    ):


        self.path = path

        self.config = {}

        self.load()





    def load(self):


        if not os.path.exists(

            self.path

        ):

            raise Exception(

                f"No existe configuración: {self.path}"

            )



        with open(

            self.path,

            "r",

            encoding="utf-8"

        ) as file:


            self.config = json.load(

                file

            )





    def get(self, *keys):


        value = self.config


        for key in keys:


            if key not in value:

                return None


            value = value[key]



        return value





    def get_window_title(self):

        return self.get(

            "window",

            "title"

        )





    def get_process_name(self):

        return self.get(

            "window",

            "process"

        )





    def get_capture_size(self):


        return (

            self.get(

                "capture",

                "width"

            ),


            self.get(

                "capture",

                "height"

            )

        )