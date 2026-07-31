from core.models.player_state import PlayerState





class PlayerMonitor:


    def __init__(

        self,

        detector,

        resolver,

        bar_reader,

        templates,

        name_matcher,

        entity_cache

    ):


        self.detector = detector

        self.resolver = resolver

        self.bar_reader = bar_reader

        self.templates = templates

        self.name_matcher = name_matcher

        self.entity_cache = entity_cache







    # =====================================
    # UPDATE
    # =====================================


    def update(

        self,

        image,

        player_state: PlayerState

    ):


        if image is None:

            return False





        player_anchor_template = self.templates.get(

            "player_anchor"

        )



        player_anchor = self.detector.detect(

            image,

            player_anchor_template

        )



        if not player_anchor:

            player_state.reset()

            return False






        hud_template = self.templates.get(

            "player_hud"

        )



        player_hud = self.resolver.resolve(

            player_anchor,

            hud_template

        )



        if not player_hud:

            player_state.reset()

            return False






        hud_image = self.resolver.crop(

            image,

            player_hud

        )



        if hud_image is None:

            return False







        # =====================================
        # IDENTIDAD
        # =====================================


        self.read_identity(

            hud_image,

            player_state

        )







        # =====================================
        # HP
        # =====================================


        hp_region = self.templates.get(

            "player_hp"

        )


        hp_image = self.crop_region(

            hud_image,

            hp_region

        )



        player_state.hp_percent = self.bar_reader.read_hp(

            hp_image

        )







        # =====================================
        # MP
        # =====================================


        mp_region = self.templates.get(

            "player_mp"

        )


        mp_image = self.crop_region(

            hud_image,

            mp_region

        )



        player_state.mp_percent = self.bar_reader.read_mp(

            mp_image

        )





        return True







    # =====================================
    # OCR IDENTIDAD
    # =====================================


    def read_identity(

        self,

        hud_image,

        player_state

    ):



        # Nombre una única vez

        if self.entity_cache.need_player_name():


            region = self.templates.get(

                "player_name"

            )


            name_image = self.crop_region(

                hud_image,

                region

            )


            name = self.name_matcher.read_player_name(

                name_image

            )



            if name:


                player_state.name = name


                self.entity_cache.player_name_loaded_ok()







        # Nivel cada 30 minutos


        if self.entity_cache.need_player_level():


            region = self.templates.get(

                "player_level"

            )



            level_image = self.crop_region(

                hud_image,

                region

            )



            level = self.name_matcher.read_number(

                level_image

            )



            if level > 0:

                player_state.level = level



            self.entity_cache.update_player_level_time()







    # =====================================
    # CROP
    # =====================================


    def crop_region(

        self,

        image,

        region

    ):


        if image is None:

            return None



        if region is None:

            return None



        return image[

            region["y"]:

            region["y"] + region["height"],


            region["x"]:

            region["x"] + region["width"]

        ]