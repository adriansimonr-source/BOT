from core.models.game_state import GameState

from core.managers.vision_manager import VisionManager





class GameStateManager:


    def __init__(

        self,

        process_manager

    ):


        self.process_manager = process_manager


        # =====================================
        # Estado global del juego
        # =====================================

        self.state = GameState()



        # =====================================
        # Sistema visión
        # =====================================
        #
        # IMPORTANTE:
        # No crear VisionManager aquí.
        # Este objeto debe nacer dentro
        # del hilo del bot.
        #

        self.vision = None



        self.running = False







    # =====================================
    # START
    # =====================================


    def start(self):


        if self.running:

            return





        # Crear VisionManager dentro
        # del hilo que ejecuta el bot

        if self.vision is None:


            self.vision = VisionManager()



        self.vision.start()



        self.running = True



        print(

            "[GameStateManager] iniciado"

        )









    # =====================================
    # UPDATE
    # =====================================


    def update(self):


        if not self.process_manager.is_connected():


            self.state.connected = False


            return





        self.state.connected = True






        if not self.running:

            return






        # Actualizar visión


        if self.vision:


            self.vision.update(

                self.state

            )









    # =====================================
    # POSITION CONTROL
    # =====================================


    def lock_player_position(self):


        self.state.player.lock_position()



        print(

            "[GameStateManager] posición inicial fijada",

            self.state.player.start_x,

            self.state.player.start_y

        )









    def unlock_player_position(self):


        self.state.player.unlock_position()



        print(

            "[GameStateManager] posición inicial liberada"

        )









    def refresh_player_position(self):


        if self.vision:


            self.vision.reset_position_reader()



        print(

            "[GameStateManager] refrescando posición"

        )









    # =====================================
    # STOP
    # =====================================


    def stop(self):


        if not self.running:

            return





        if self.vision:


            self.vision.stop()





        self.running = False



        print(

            "[GameStateManager] detenido"

        )









    # =====================================
    # STATE ACCESS
    # =====================================


    def get_state(self):


        return self.state