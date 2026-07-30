class Detection:


    def __init__(self):

        self.changed = False

        self.score = 0.0

        self.regions = []



    def add_region(

        self,

        region

    ):

        self.regions.append(region)



    def info(self):

        return {

            "changed": self.changed,

            "score": self.score,

            "regions": len(self.regions)

        }