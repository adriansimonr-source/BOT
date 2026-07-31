from core.models.player_state import PlayerState





class PlayerMonitor:


    def __init__(

        self,

        detector,

        resolver,

        bar_reader,

        templates,

        name_matcher

    ):


        self.detector = detector

        self.resolver = resolver

        self.bar_reader = bar_reader

        self.templates = templates

        self.name_matcher = name_matcher







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



        player_anchor = self.detector.detect(

            image,

            anchor_template

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

            player_state.reset()

            return False







        # =========================
        # NOMBRE
        # =========================


        name_region = self.templates.get(

            "player_name"

        )


        name_image = self.crop_region(

            hud_image,

            name_region

        )


        if name_image is not None:


            name = self.name_matcher.match_player(

                name_image

            )


            if name:

                player_state.name = name








        # =========================
        # NIVEL
        # =========================


        # Reservado para reconocimiento futuro

        level_region = self.templates.get(

            "player_level"

        )







        # =========================
        # HP
        # =========================


        hp_region = self.templates.get(

            "player_hp"

        )


        hp_image = self.crop_region(

            hud_image,

            hp_region

        )


        player_state.hp_percent = (

            self.bar_reader.read_hp(

                hp_image

            )

        )







        # =========================
        # MP
        # =========================


        mp_region = self.templates.get(

            "player_mp"

        )


        mp_image = self.crop_region(

            hud_image,

            mp_region

        )


        player_state.mp_percent = (

            self.bar_reader.read_mp(

                mp_image

            )

        )




        return True







    def crop_region(

        self,

        image,

        region

    ):


        if image is None or region is None:

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



        return image[

            y:y + height,

            x:x + width

        ]