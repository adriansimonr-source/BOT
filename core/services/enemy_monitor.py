from core.models.target_state import TargetState





class EnemyMonitor:


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

        target_state: TargetState

    ):


        if image is None:

            return False





        anchor_template = self.templates.get(

            "enemy_anchor"

        )


        if anchor_template is None:

            return False





        enemy_anchor = self.detector.detect(

            image,

            anchor_template

        )



        # No hay objetivo visible

        if not enemy_anchor:


            target_state.exists = False

            target_state.hp_percent = 0


            return False







        hud_template = self.templates.get(

            "enemy_hud"

        )


        if hud_template is None:

            return False





        enemy_hud = self.resolver.resolve(

            enemy_anchor,

            hud_template

        )



        if not enemy_hud:

            return False







        hud_image = self.resolver.crop(

            image,

            enemy_hud

        )



        if hud_image is None:

            return False







        self.read_identity(

            hud_image,

            target_state

        )



        self.read_health(

            hud_image,

            target_state

        )





        target_state.exists = True



        return True







    # =====================================
    # IDENTIDAD
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



        if name_image is None:

            return







        name = self.name_matcher.read_enemy_name(

            name_image

        )



        if not self.valid_name(name):

            return







        # Resolver contra base de datos

        name = self.entity_database.resolve_enemy_name(

            name

        )



        if not name:

            return







        # Enemigo nuevo o cambiado

        if self.entity_cache.enemy_changed(

            name

        ):


            level = 0



            level_region = self.templates.get(

                "enemy_level"

            )


            level_image = self.crop_region(

                hud_image,

                level_region

            )



            if level_image is not None:


                level = self.name_matcher.read_number(

                    level_image

                )





            target_state.name = name

            target_state.level = level





            self.entity_cache.update_enemy(

                name,

                level

            )



            self.entity_database.register_enemy_seen(

                name

            )





        else:


            target_state.name = (

                self.entity_cache.current_enemy_name

            )


            target_state.level = (

                self.entity_cache.current_enemy_level

            )









    # =====================================
    # VIDA
    # =====================================


    def read_health(

        self,

        hud_image,

        target_state

    ):


        hp_region = self.templates.get(

            "enemy_hp"

        )



        hp_image = self.crop_region(

            hud_image,

            hp_region

        )



        if hp_image is None:

            return





        target_state.hp_percent = (

            self.bar_reader.read_enemy_hp(

                hp_image

            )

        )









    # =====================================
    # VALIDACION
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