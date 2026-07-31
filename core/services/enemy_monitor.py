from core.models.target_state import TargetState





class EnemyMonitor:


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

            self.entity_cache.clear_enemy()

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

            return False







        # =====================================
        # IDENTIDAD ENEMIGO
        # =====================================


        self.read_identity(

            hud_image,

            target_state

        )







        # =====================================
        # HP
        # =====================================


        hp_region = self.templates.get(

            "enemy_hp"

        )



        hp_image = self.crop_region(

            hud_image,

            hp_region

        )



        target_state.hp_percent = self.bar_reader.read_enemy_hp(

            hp_image

        )



        target_state.exists = True



        return True







    # =====================================
    # OCR ENEMIGO
    # =====================================


    def read_identity(

        self,

        hud_image,

        target_state

    ):


        name_region = self.templates.get(

            "enemy_name"

        )


        name_image = self.crop_region(

            hud_image,

            name_region

        )



        name = self.name_matcher.read_enemy_name(

            name_image

        )



        if not name:

            return





        if self.entity_cache.enemy_changed(

            name

        ):


            level_region = self.templates.get(

                "enemy_level"

            )


            level_image = self.crop_region(

                hud_image,

                level_region

            )


            level = self.name_matcher.read_number(

                level_image

            )



            target_state.name = name

            target_state.level = level



            self.entity_cache.update_enemy(

                name,

                level

            )



        else:


            target_state.name = (

                self.entity_cache.current_enemy_name

            )


            target_state.level = (

                self.entity_cache.current_enemy_level

            )









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