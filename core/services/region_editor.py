import cv2
import json
import os




class RegionEditor:


    def __init__(

        self,

        image

    ):


        self.image = image.copy()


        self.start = None

        self.end = None


        self.regions = []





    # =====================================
    # Mouse callback
    # =====================================


    def mouse(

        self,

        event,

        x,

        y,

        flags,

        param

    ):


        if event == cv2.EVENT_LBUTTONDOWN:


            self.start = (

                x,

                y

            )


            self.end = (

                x,

                y

            )





        elif event == cv2.EVENT_MOUSEMOVE:


            if self.start is not None:


                self.end = (

                    x,

                    y

                )





        elif event == cv2.EVENT_LBUTTONUP:


            self.end = (

                x,

                y

            )


            self.create_region()







    # =====================================
    # Crear región
    # =====================================


    def create_region(self):


        if self.start is None or self.end is None:

            return




        x1, y1 = self.start

        x2, y2 = self.end





        x = min(

            x1,

            x2

        )


        y = min(

            y1,

            y2

        )



        width = abs(

            x2 - x1

        )


        height = abs(

            y2 - y1

        )






        if width == 0 or height == 0:

            return





        name = input(

            "Nombre región: "

        )



        if not name:

            return





        region = {


            "name": name,


            "x": x,


            "y": y,


            "width": width,


            "height": height


        }





        self.regions.append(

            region

        )





        print(

            "Region creada:",

            name

        )





        #
        # limpiar selección
        #

        self.start = None

        self.end = None







    # =====================================
    # Ejecutar editor
    # =====================================


    def run(self):


        window = "REGION EDITOR"



        cv2.namedWindow(

            window

        )



        cv2.setMouseCallback(

            window,

            self.mouse

        )






        while True:



            frame = self.image.copy()





            if self.start and self.end:


                cv2.rectangle(

                    frame,

                    self.start,

                    self.end,

                    (0,255,0),

                    2

                )






            #
            # Mostrar regiones creadas
            #

            for region in self.regions:



                cv2.rectangle(

                    frame,

                    (

                        region["x"],

                        region["y"]

                    ),

                    (

                        region["x"] + region["width"],

                        region["y"] + region["height"]

                    ),

                    (255,0,0),

                    2

                )



                cv2.putText(

                    frame,

                    region["name"],

                    (

                        region["x"],

                        region["y"] - 5

                    ),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (255,0,0),

                    2

                )








            cv2.imshow(

                window,

                frame

            )





            key = cv2.waitKey(20)





            #
            # Guardar
            #

            if key == ord("s"):


                self.save(

                    "data/regions.json"

                )


                print(

                    "Regiones guardadas"

                )






            #
            # salir
            #

            if key == 27:


                break





        cv2.destroyAllWindows()







    # =====================================
    # Guardar JSON
    # =====================================


    def save(

        self,

        path

    ):



        folder = os.path.dirname(

            path

        )



        if folder:


            os.makedirs(

                folder,

                exist_ok=True

            )







        with open(

            path,

            "w",

            encoding="utf-8"

        ) as file:



            json.dump(

                self.regions,

                file,

                indent=4,

                ensure_ascii=False

            )



        print(

            "Guardado:",

            path

        )