import cv2
import os



class TemplateCreator:


    def __init__(self, image):


        self.image = image.copy()


        self.start = None

        self.end = None


        self.counter = 0






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


            self.end = self.start






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


            template = self.crop()



            if template is not None:


                self.save(

                    template

                )






            self.start = None

            self.end = None







    def crop(self):


        if self.start is None or self.end is None:

            return None



        x1,y1 = self.start

        x2,y2 = self.end



        x = min(

            x1,

            x2

        )


        y = min(

            y1,

            y2

        )


        w = abs(

            x2-x1

        )


        h = abs(

            y2-y1

        )



        if w < 5 or h < 5:

            return None



        return self.image[

            y:y+h,

            x:x+w

        ]







    def save(

        self,

        image

    ):



        os.makedirs(

            "data/templates",

            exist_ok=True

        )



        self.counter += 1



        path = (

            f"data/templates/template_{self.counter}.png"

        )



        cv2.imwrite(

            path,

            image

        )



        print(

            "[OK] Template guardado:",

            path

        )







    def run(self):


        window = "TEMPLATE CREATOR"



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



            cv2.imshow(

                window,

                frame

            )



            key = cv2.waitKey(20)



            if key == 27:

                break



        cv2.destroyAllWindows()