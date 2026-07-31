import json
import os
import cv2

from core.models.template import Template





class TemplateManager:


    def __init__(

        self,

        config_path="data/templates.json"

    ):


        self.templates = {}

        self.config_path = config_path


        self.load()






    # =====================================
    # LOAD
    # =====================================


    def load(self):


        if not os.path.exists(

            self.config_path

        ):

            raise Exception(

                f"No existe configuración: {self.config_path}"

            )





        with open(

            self.config_path,

            "r",

            encoding="utf-8"

        ) as file:


            data = json.load(file)





        self.load_anchors(

            data.get(

                "anchors",

                {}

            )

        )



        self.load_regions(

            data.get(

                "regions",

                {}

            )

        )








    # =====================================
    # ANCHORS
    # =====================================


    def load_anchors(

        self,

        anchors

    ):


        for name, info in anchors.items():


            filename = info.get(

                "file"

            )


            if filename is None:


                raise Exception(

                    f"Anchor sin file: {name}"

                )





            template = Template(

                name=name,

                path=self.build_path(

                    filename,

                    "anchors"

                ),

                template_type="anchor",

                threshold=info.get(

                    "threshold",

                    0.85

                )

            )





            self.load_image(

                template

            )



            self.templates[name] = template



            print(

                "[OK] Anchor cargado:",

                name

            )









    # =====================================
    # REGIONS
    # =====================================


    def load_regions(

        self,

        regions

    ):


        for name, info in regions.items():


            region = {


                "name": name,


                "type": info.get(

                    "type",

                    "region"

                ),


                "parent": info.get(

                    "parent"

                ),


                "x": info.get(

                    "x",

                    0

                ),


                "y": info.get(

                    "y",

                    0

                ),


                "width": info.get(

                    "width",

                    0

                ),


                "height": info.get(

                    "height",

                    0

                ),


                "bar_type": info.get(

                    "bar_type"

                ),


                "color": info.get(

                    "color"

                )

            }





            self.templates[name] = region



            print(

                "[OK] Region cargada:",

                name,

                "->",

                region["parent"]

            )








    # =====================================
    # PATH
    # =====================================


    def build_path(

        self,

        filename,

        folder

    ):


        return os.path.join(

            "data",

            "templates",

            folder,

            filename

        )









    # =====================================
    # IMAGE
    # =====================================


    def load_image(

        self,

        template

    ):


        if not os.path.exists(

            template.path

        ):


            raise Exception(

                f"No existe template: {template.path}"

            )





        image = cv2.imread(

            template.path,

            cv2.IMREAD_COLOR

        )



        if image is None:


            raise Exception(

                f"No se pudo cargar: {template.path}"

            )





        template.image = image









    # =====================================
    # GET
    # =====================================


    def get(

        self,

        name

    ):


        return self.templates.get(

            name

        )









    # =====================================
    # LIST
    # =====================================


    def list(self):


        return list(

            self.templates.keys()

        )









    # =====================================
    # FILTER ANCHORS
    # =====================================


    def get_anchors(self):


        return [

            template

            for template in self.templates.values()

            if isinstance(

                template,

                Template

            )

        ]









    # =====================================
    # FILTER REGIONS
    # =====================================


    def get_regions(self):


        return [

            region

            for region in self.templates.values()

            if isinstance(

                region,

                dict

            )

        ]









    # =====================================
    # FILTER BY TYPE
    # =====================================


    def get_by_type(

        self,

        template_type

    ):


        return [

            template

            for template in self.templates.values()

            if isinstance(

                template,

                dict

            )

            and template.get(

                "type"

            ) == template_type

        ]