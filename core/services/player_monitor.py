from core.models.player_state import PlayerState





class PlayerMonitor:


    def __init__(

        self,

        detector,

        resolver,

        bar_reader,

        templates,

        name_matcher,

        entity_cache,

        entity_database

    ):


        self.detector = detector

        self.resolver = resolver

        self.bar_reader = bar_reader

        self.templates = templates

        self.name_matcher = name_matcher

        self.entity_cache = entity_cache

        self.entity_database = entity_database







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





        anchor_template = self.templates.get(

            "player_anchor"

        )



        if anchor_template is None:

            return False





        player_anchor = self.detector.detect(

            image,

            anchor_template

        )



        if not player_anchor:

            return False







        hud_template = self.templates.get(

            "player_hud"

        )



        if hud_template is None:

            return False





        player_hud = self.resolver.resolve(

            player_anchor,

            hud_template

        )



        if not player_hud:

            return False







        hud_image = self.resolver.crop(

            image,

            player_hud

        )



        if hud_image is None:

            return False







        self.read_identity(

            hud_image,

            player_state

        )





        self.read_resources(

            hud_image,

            player_state

        )





        return True







    # =====================================
    # IDENTIDAD
    # =====================================


    def read_identity(

        self,

        hud_image,

        player_state

    ):



        # ==========================
        # NOMBRE
        # ==========================


        if self.entity_cache.need_player_name():


            region = self.templates.get(

                "player_name"

            )


            name_image = self.crop_region(

                hud_image,

                region

            )


            if name_image is not None:


                name = self.name_matcher.read_player_name(

                    name_image

                )



                if self.valid_name(name):


                    name = self.entity_database.resolve_player_name(

                        name

                    )



                    if name:


                        player_state.name = name


                        self.entity_cache.player_name_loaded_ok()







        # ==========================
        # NIVEL
        # ==========================


        if self.entity_cache.need_player_level():


            region = self.templates.get(

                "player_level"

            )


            level_image = self.crop_region(

                hud_image,

                region

            )



            if level_image is not None:


                level = self.name_matcher.read_number(

                    level_image

                )



                if level > 0:


                    player_state.level = level





            self.entity_cache.update_player_level_time()







    # =====================================
    # RECURSOS
    # =====================================


    def read_resources(

        self,

        hud_image,

        player_state

    ):


        hp_region = self.templates.get(

            "player_hp"

        )


        hp_image = self.crop_region(

            hud_image,

            hp_region

        )


        if hp_image is not None:


            player_state.hp_percent = (

                self.bar_reader.read_hp(

                    hp_image

                )

            )







        mp_region = self.templates.get(

            "player_mp"

        )


        mp_image = self.crop_region(

            hud_image,

            mp_region

        )


        if mp_image is not None:


            player_state.mp_percent = (

                self.bar_reader.read_mp(

                    mp_image

                )

            )









    # =====================================
    # VALIDACION NOMBRE
    # =====================================


    def valid_name(

        self,

        name

    ):


        if not name:

            return False



        if len(name) < 2:

            return False



        return True







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





        x = region.get(

            "x",

            0

        )


        y = region.get(

            "y",

            0

        )


        width = region.get(

            "width",

            0

        )


        height = region.get(

            "height",

            0

        )



        if width <= 0 or height <= 0:

            return None





        return image[

            y:y + height,

            x:x + width

        ]