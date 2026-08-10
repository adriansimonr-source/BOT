from enum import Enum, auto



class TargetDecision(Enum):

    ALLOW = auto()

    REJECT = auto()



class TargetRules:


    def __init__(self):

        self.blacklist = []

        self.unique_targets = []


        self.blacklist_enabled = False

        self.unique_targets_enabled = False



        self.min_level = 0

        self.max_level = 999





    # =====================================
    # CONFIGURATION
    # =====================================


    def set_blacklist(
        self,
        names,
        enabled=False
    ):

        self.blacklist = self._normalize_names(
            names
        )

        self.blacklist_enabled = bool(
            enabled and self.blacklist
        )





    def set_unique_targets(
        self,
        names,
        enabled=False
    ):

        self.unique_targets = self._normalize_names(
            names
        )

        self.unique_targets_enabled = bool(
            enabled and self.unique_targets
        )





    def add_blacklist(
        self,
        name
    ):

        normalized = self._normalize_name(
            name
        )


        if normalized and normalized not in self.blacklist:

            self.blacklist.append(
                normalized
            )





    def remove_blacklist(
        self,
        name
    ):

        normalized = self._normalize_name(
            name
        )


        if normalized in self.blacklist:

            self.blacklist.remove(
                normalized
            )





    # =====================================
    # FILTER STATUS
    # =====================================


    def has_filters(self):

        return (

            self.blacklist_enabled

            or

            self.unique_targets_enabled

        )





    # =====================================
    # EVALUATION
    # =====================================


    def evaluate(
        self,
        target
    ):


        # Sin objetivo

        if not target.exists:

            return TargetDecision.REJECT





        # =================================
        # SIN FILTROS
        # =================================
        #
        # No importa:
        # - nombre
        # - OCR
        # - entidad
        # - nivel
        #

        if not self.has_filters():

            return TargetDecision.ALLOW





        name = self._normalize_name(
            target.name
        )





        # =================================
        # FILTRO IGNORADOS
        # =================================


        if self.blacklist_enabled:


            if name in self.blacklist:

                return TargetDecision.REJECT





        # =================================
        # FILTRO OBJETIVOS UNICOS
        # =================================


        if self.unique_targets_enabled:


            if name not in self.unique_targets:

                return TargetDecision.REJECT





        # =================================
        # NIVEL
        # =================================


        if (
            target.level < self.min_level
            or
            target.level > self.max_level
        ):

            return TargetDecision.REJECT





        return TargetDecision.ALLOW







    def is_allowed(
        self,
        target
    ):

        return (

            self.evaluate(target)

            is

            TargetDecision.ALLOW

        )







    # =====================================
    # NORMALIZATION
    # =====================================


    @classmethod
    def _normalize_names(
        cls,
        names
    ):

        return list(
            dict.fromkeys(

                normalized

                for name in names

                if (

                    normalized := cls._normalize_name(
                        name
                    )

                )

            )
        )





    @staticmethod
    def _normalize_name(
        name
    ):

        return str(
            name or ""
        ).strip().casefold()