class PlayerState:


    def __init__(self):


        # ==============================
        # IDENTIDAD
        # ==============================

        self.name = ""

        self.level = 0





        # ==============================
        # RECURSOS
        # ==============================

        self.hp_percent = 0

        self.mp_percent = 0





        # ==============================
        # POSICIÓN ACTUAL (OCR)
        # ==============================

        # Posición que detecta el juego
        # en tiempo real

        self.x = 0

        self.y = 0

        self.z = 0






        # ==============================
        # POSICIÓN INICIAL BLOQUEADA
        # ==============================

        # Referencia que usará el bot

        self.start_x = 0

        self.start_y = 0



        # Indica si el usuario
        # ha confirmado la posición

        self.position_locked = False






        # ==============================
        # POSICIÓN MINIMAPA
        # ==============================

        self.minimap_position = None







    # ==================================
    # ACTUALIZAR POSICIÓN OCR
    # ==================================

    def update_position(

        self,

        x,

        y

    ):


        self.x = x

        self.y = y






    # ==================================
    # BLOQUEAR POSICIÓN INICIAL
    # ==================================

    def lock_position(self):


        self.start_x = self.x

        self.start_y = self.y


        self.position_locked = True



        print(

            "[PLAYER POSITION LOCKED]",

            self.start_x,

            self.start_y

        )








    # ==================================
    # DESBLOQUEAR POSICIÓN
    # ==================================

    def unlock_position(self):


        self.position_locked = False


        self.start_x = 0

        self.start_y = 0






    # ==================================
    # RESET
    # ==================================

    def reset(self):


        self.name = ""

        self.level = 0



        self.hp_percent = 0

        self.mp_percent = 0




        self.x = 0

        self.y = 0

        self.z = 0





        self.start_x = 0

        self.start_y = 0



        self.position_locked = False



        self.minimap_position = None







    # ==================================
    # EXPORT
    # ==================================

    def to_dict(self):


        return {


            "name": self.name,


            "level": self.level,



            "hp_percent": self.hp_percent,


            "mp_percent": self.mp_percent,



            # posición actual OCR

            "x": self.x,


            "y": self.y,


            "z": self.z,



            # posición inicial bot

            "start_x": self.start_x,


            "start_y": self.start_y,



            "position_locked":

                self.position_locked

        }