class Region:


    def __init__(

        self,

        name,

        x,

        y,

        width,

        height

    ):


        self.name = name

        self.x = x

        self.y = y

        self.width = width

        self.height = height



    def crop(self, image):

        return image[

            self.y:self.y+self.height,

            self.x:self.x+self.width

        ]



    def to_dict(self):

        return {

            "name":self.name,

            "x":self.x,

            "y":self.y,

            "width":self.width,

            "height":self.height

        }