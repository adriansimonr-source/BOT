from core.models.game_state import GameState

from core.managers.vision_manager import VisionManager





class GameStateManager:


    def __init__(

        self,

        process_manager

    ):


        self.process_manager = process_manager


        # Estado global del juego

        self.state = GameState()



        # Sistema de visión

        self.vision = VisionManager()



        self.running = False






    # =====================================
    # START
    # =====================================


    def start(self):


        if self.running:

            return



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

        self.vision.update(

            self.state

        )









    # =====================================
    # STOP
    # =====================================


    def stop(self):


        if not self.running:

            return



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