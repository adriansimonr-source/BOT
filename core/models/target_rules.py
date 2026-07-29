class TargetRules:


    def __init__(self):

        # =====================================
        # Lista negra
        # =====================================

        # Objetivos que nunca se seleccionan

        self.blacklist = []


        # =====================================
        # Filtros de nivel
        # =====================================

        self.min_level = 0

        self.max_level = 999



        # =====================================
        # Opciones generales
        # =====================================

        # Permitir enemigos sin nombre

        self.allow_unknown = False



    # =====================================
    # Añadir / eliminar blacklist
    # =====================================

    def add_blacklist(
        self,
        name: str
    ):

        if name not in self.blacklist:

            self.blacklist.append(
                name
            )



    def remove_blacklist(
        self,
        name: str
    ):

        if name in self.blacklist:

            self.blacklist.remove(
                name
            )



    # =====================================
    # Validación objetivo
    # =====================================

    def is_allowed(
        self,
        target
    ):


        # ------------------------------
        # No existe
        # ------------------------------

        if not target.exists:

            return False



        # ------------------------------
        # Nombre vacío
        # ------------------------------

        if (
            not target.name
            and not self.allow_unknown
        ):

            return False



        # ------------------------------
        # Blacklist
        # ------------------------------

        if target.name in self.blacklist:

            return False



        # ------------------------------
        # Nivel
        # ------------------------------

        if target.level < self.min_level:

            return False


        if target.level > self.max_level:

            return False



        return True