from enum import Enum, auto


from core.modules.auto_target import AutoTarget
from core.modules.auto_attack import AutoAttack
from core.modules.auto_loot import AutoLoot
from core.modules.buff_manager import BuffManager
from core.modules.rotation_manager import RotationManager


from core.managers.game_state_manager import GameStateManager

from core.models.player_profile import PlayerProfile





class BotState(Enum):

    STOPPED = auto()

    RUNNING = auto()

    PAUSED = auto()






class BotEngine:


    def __init__(

        self,

        game_state_manager: GameStateManager

    ):


        self.state = BotState.STOPPED


        self.game_state_manager = game_state_manager



        # =====================================
        # Perfil actual
        # =====================================


        self.profile = PlayerProfile()





        # =====================================
        # Módulos
        # =====================================


        self.modules = []


        self.register_module(

            AutoTarget()

        )


        self.register_module(

            AutoAttack()

        )


        self.register_module(

            AutoLoot()

        )


        self.register_module(

            BuffManager()

        )


        self.register_module(

            RotationManager()

        )








    # =====================================
    # Gestión módulos
    # =====================================


    def register_module(

        self,

        module

    ):


        self.modules.append(

            module

        )





    def unregister_module(

        self,

        module

    ):


        if module in self.modules:

            self.modules.remove(

                module

            )





    def get_modules(self):

        return self.modules






    def get_module(

        self,

        module_type

    ):


        for module in self.modules:


            if isinstance(

                module,

                module_type

            ):

                return module



        return None







    # =====================================
    # Perfil
    # =====================================


    def get_profile(self):

        return self.profile








    # =====================================
    # Configuración
    # =====================================


    def configure(

        self,

        right_panel,

        center_panel

    ):


        for module in self.modules:


            if hasattr(

                module,

                "configure"

            ):


                module.configure(

                    right_panel,

                    center_panel

                )









    # =====================================
    # Control
    # =====================================


    def start(self):


        if self.state == BotState.RUNNING:

            return





        self.state = BotState.RUNNING





        # Iniciar captura y visión

        self.game_state_manager.start()





        for module in self.modules:


            module.on_start()





        print(

            "Bot iniciado"

        )









    def stop(self):


        if self.state == BotState.STOPPED:

            return





        self.state = BotState.STOPPED





        # Detener captura y visión

        self.game_state_manager.stop()





        for module in self.modules:


            module.on_stop()





        print(

            "Bot detenido"

        )









    def pause(self):


        if self.state != BotState.RUNNING:

            return





        self.state = BotState.PAUSED



        print(

            "Bot pausado"

        )









    def resume(self):


        if self.state != BotState.PAUSED:

            return





        self.state = BotState.RUNNING



        print(

            "Bot reanudado"

        )









    # =====================================
    # Game Loop
    # =====================================


    def update(self):


        if self.state != BotState.RUNNING:

            return





        # Actualizar estado del juego

        self.game_state_manager.update()





        state = (

            self.game_state_manager.get_state()

        )





        # Debug temporal de visión

        player = state.player



        print(

            f"{player.name} "

            f"HP:{player.hp_percent}% "

            f"MP:{player.mp_percent}%"

        )







        # Ejecutar módulos

        for module in self.modules:


            if not module.is_enabled():

                continue





            if not module.should_update():

                continue





            module.update(

                state

            )









    # =====================================
    # Consultas
    # =====================================


    def is_running(self):

        return (

            self.state == BotState.RUNNING

        )





    def is_paused(self):

        return (

            self.state == BotState.PAUSED

        )





    def is_stopped(self):

        return (

            self.state == BotState.STOPPED

        )





    def get_state(self):

        return self.state