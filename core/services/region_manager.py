import json


class RegionManager:


    def __init__(self):

        self.regions = {}



    # =====================================
    # Añadir región
    # =====================================

    def add(

        self,

        region

    ):

        self.regions[

            region.name

        ] = region





    # =====================================
    # Obtener región
    # =====================================

    def get(

        self,

        name

    ):

        return self.regions.get(name)





    # =====================================
    # Existe
    # =====================================

    def exists(

        self,

        name

    ):

        return name in self.regions





    # =====================================
    # Eliminar
    # =====================================

    def remove(

        self,

        name

    ):


        if name in self.regions:

            del self.regions[name]





    # =====================================
    # Lista regiones
    # =====================================

    def all(self):

        return list(

            self.regions.values()

        )





    # =====================================
    # Limpiar
    # =====================================

    def clear(self):

        self.regions.clear()





    # =====================================
    # Guardar configuración
    # =====================================

    def save(

        self,

        path

    ):


        data = [

            region.to_dict()

            for region in self.regions.values()

        ]



        with open(

            path,

            "w",

            encoding="utf-8"

        ) as file:


            json.dump(

                data,

                file,

                indent=4,

                ensure_ascii=False

            )





    # =====================================
    # Cargar configuración
    # =====================================

    def load(

        self,

        path,

        region_class

    ):


        with open(

            path,

            "r",

            encoding="utf-8"

        ) as file:


            data = json.load(file)




        for item in data:


            self.add(

                region_class(

                    item["name"],

                    item["x"],

                    item["y"],

                    item["width"],

                    item["height"]

                )

            )





    # =====================================
    # Debug
    # =====================================

    def info(self):

        return {

            "count": len(self.regions),

            "regions": list(

                self.regions.keys()

            )

        }