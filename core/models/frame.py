class Frame:


    def __init__(

        self,

        image,

        timestamp

    ):


        self.image = image

        self.timestamp = timestamp


        self.height = image.shape[0]

        self.width = image.shape[1]


    def info(self):


        return {

            "width": self.width,

            "height": self.height,

            "timestamp": self.timestamp

        }