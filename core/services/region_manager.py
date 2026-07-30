class RegionManager:


    def __init__(self):

        self.regions = {}



    def add(

        self,

        region

    ):

        self.regions[
            region.name
        ] = region



    def get(

        self,

        name

    ):

        return self.regions[name]