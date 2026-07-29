from enum import Enum


# ==================================================
# Modos de funcionamiento del bot
# ==================================================

class BotMode(Enum):

    # Puede moverse dentro del radio indicado

    STATIC_100 = 100

    STATIC_250 = 250

    STATIC_500 = 500


    # Sin límite

    OFF = -1


    # No se mueve del punto inicial

    STATIC_POINT = 0



# ==================================================
# Configuración del bot
# ==================================================

class BotSettings:


    def __init__(self):

        # =====================================
        # Modo actual
        # =====================================

        self.mode = BotMode.STATIC_250


        # =====================================
        # Punto inicial
        # =====================================

        self.start_x = None
        self.start_y = None
        self.start_z = None


        # =====================================
        # Movimiento
        # =====================================

        # Volver cuando salga del área

        self.auto_return = True


        # Segundos antes de iniciar retorno

        self.return_delay = 10



        # =====================================
        # Selección de objetivos
        # =====================================

        # Distancia para detectar objetivos

        self.target_range = 100



        # =====================================
        # Estado interno
        # =====================================

        self.returning = False



    # ==================================================
    # Distancia máxima de movimiento
    # ==================================================

    def get_movement_range(self):

        # Sin límite

        if self.mode == BotMode.OFF:

            return None


        # Punto fijo

        if self.mode == BotMode.STATIC_POINT:

            return 0


        return self.mode.value



    # ==================================================
    # Distancia de selección de objetivos
    # ==================================================

    def get_target_range(self):

        return self.target_range



    # ==================================================
    # Consultas
    # ==================================================

    def is_unlimited(self):

        return (
            self.mode == BotMode.OFF
        )


    def is_static_point(self):

        return (
            self.mode == BotMode.STATIC_POINT
        )


    def can_move(self):

        return not self.is_static_point()



    # ==================================================
    # Posición inicial
    # ==================================================

    def set_start_position(
        self,
        x,
        y,
        z=0
    ):

        self.start_x = x
        self.start_y = y
        self.start_z = z



    # ==================================================
    # Cambio de modo
    # ==================================================

    def set_mode(
        self,
        mode: BotMode
    ):

        self.mode = mode