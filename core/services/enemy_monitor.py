from core.models.target_state import TargetState





class EnemyMonitor:


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

        target_state: TargetState

    ):


        if image is None:

            return False





        anchor_template = self.templates.get(

            "enemy_anchor"

        )



        enemy_anchor = self.detector.detect(

            image,

            anchor_template

        )



        if not enemy_anchor:


            target_state.reset()

            return False







        hud_template = self.templates.get(

            "enemy_hud"

        )



        enemy_hud = self.resolver.resolve(

            enemy_anchor,

            hud_template

        )



        if not enemy_hud:


            target_state.reset()

            return False







        hud_image = self.resolver.crop(

            image,

            enemy_hud

        )



        if hud_image is None:


            target_state.reset()

            return False








        target_state.exists = True







        # =========================
        # NOMBRE
        # =========================


        name_region = self.templates.get(

            "enemy_name"

        )


        name_image = self.crop_region(

            hud_image,

            name_region

        )



        if name_image is not None:


            name = self.name_matcher.match_enemy(

                name_image

            )


            if name:

                target_state.name = name







        # =========================
        # NIVEL
        # =========================


        level_region = self.templates.get(

            "enemy_level"

        )

        # Preparado para futuro







        # =========================
        # HP
        # =========================


        hp_region = self.templates.get(

            "enemy_hp"

        )



        hp_image = self.crop_region(

            hud_image,

            hp_region

        )



        target_state.hp_percent = (

            self.bar_reader.read_enemy_hp(

                hp_image

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