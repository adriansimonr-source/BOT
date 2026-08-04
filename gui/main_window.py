from PySide6.QtCore import (
    QThread,
    QTimer,
    Signal,
)

from PySide6.QtGui import QIcon

from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QTabWidget,
    QLabel,
    QMessageBox,
)


from gui.tabs.bot_tab import BotTab
from gui.dialogs.add_game_dialog import AddGameDialog


from core.process_manager import ProcessManager
from core.managers.game_profile_manager import GameProfileManager
from core.managers.game_state_manager import GameStateManager
from core.managers.entity_database_manager import EntityDatabaseManager
from core.bot_engine import BotEngine
from core.bot_worker import BotWorker





class MainWindow(QMainWindow):


    stop_bot_requested = Signal()


    def __init__(self):

        super().__init__()


        self.configure_window()

        self.apply_style()


        self.game_profiles = GameProfileManager()


        self.process_manager = ProcessManager(

            game_profiles=self.game_profiles

        )


        self.game_state_manager = GameStateManager(

            self.process_manager

        )


        self.bot_engine = BotEngine(

            self.game_state_manager

        )


        self.entity_database = EntityDatabaseManager()


        self.bot_thread = None

        self.bot_worker = None

        self._close_pending = False



        self.create_ui()

        self.create_timer()

        self.connect_signals()


        self.initialize_selected_game()


        self.refresh_enemy_lists(force=True)






    def configure_window(self):


        self.setWindowTitle(

            "SB Automation Suite"

        )


        self.setWindowIcon(

            QIcon(

                "data/logo/Logo_cami.png"

            )

        )


        self.setFixedSize(

            750,

            500

        )









    # =====================================
    # STYLE
    # =====================================


    def apply_style(self):


        self.setStyleSheet(

            """

            QWidget {

                background-color: #FFFFFF;

                color: #173B6D;

                font-size: 12px;

            }



            QTabWidget::pane {

                border: 1px solid #D7E3F2;

                border-radius: 8px;

                background: white;

            }



            QTabBar::tab {

                background: #EAF2FB;

                color: #173B6D;

                padding: 7px 18px;

                border-radius: 6px;

                margin-right: 4px;

            }



            QTabBar::tab:selected {

                background: #173B6D;

                color: white;

            }



            QPushButton {

                background-color: #173B6D;

                color: white;

                border-radius: 6px;

                padding: 4px 8px;

            }



            QPushButton:hover {

                background-color: #28558F;

            }



            QComboBox {

                border: 1px solid #B9CBE3;

                border-radius: 6px;

                padding: 4px;

                background: white;

            }



            QProgressBar {

                border: 1px solid #B9CBE3;

                border-radius: 5px;

                background: #F4F7FB;

                height: 12px;

            }



            QProgressBar::chunk {

                background-color: #173B6D;

                border-radius: 5px;

            }

            """

        )









    # =====================================
    # UI
    # =====================================


    def create_ui(self):


        central = QWidget()


        self.setCentralWidget(

            central

        )


        layout = QVBoxLayout(

            central

        )


        layout.setContentsMargins(

            6,

            6,

            6,

            6

        )



        self.tabs = QTabWidget()



        self.bot_tab = BotTab(self.game_profiles)

        self.log_tab = QLabel(

            "LOG"

        )



        self.tabs.addTab(

            self.bot_tab,

            "BOT"

        )


        self.tabs.addTab(

            self.log_tab,

            "LOG"

        )



        layout.addWidget(

            self.tabs

        )









    # =====================================
    # TIMER
    # =====================================


    def create_timer(self):


        self.ui_timer = QTimer(self)


        self.ui_timer.setInterval(

            250

        )


        self.ui_timer.timeout.connect(

            self.update_character_ui

        )


        self.enemy_database_timer = QTimer(self)

        self.enemy_database_timer.setInterval(1000)

        self.enemy_database_timer.timeout.connect(

            self.refresh_enemy_lists

        )

        self.enemy_database_timer.start()









    # =====================================
    # SIGNALS
    # =====================================


    def connect_signals(self):


        self.bot_tab.bot_controls.start_button.clicked.connect(

            self.toggle_bot

        )


        self.bot_tab.game_selector.game_changed.connect(

            self.game_selected

        )


        self.bot_tab.game_selector.add_game_requested.connect(

            self.add_game

        )


        self.bot_tab.game_selector.update_game_requested.connect(

            self.detect_process

        )


        self.bot_tab.game_selector.delete_game_requested.connect(

            self.delete_game

        )


        self.bot_tab.character_group.refresh_position_button.clicked.connect(

            self.refresh_player_position

        )


        self.bot_tab.character_group.refresh_name_button.clicked.connect(

            self.refresh_player_name

        )


        self.bot_tab.character_group.lock_position_button.clicked.connect(

            self.lock_player_position

        )


        self.bot_tab.character_group.unlock_position_button.clicked.connect(

            self.unlock_player_position

        )


        self.bot_tab.auto_panel.enemy_ignores_changed.connect(

            self.set_enemies_ignored

        )


    def refresh_enemy_lists(self, force=False):


        changed = self.entity_database.refresh_enemies(force=force)

        if not force and not changed:

            return


        enemy_names, ignored_names = self.entity_database.get_enemy_lists()

        self.bot_tab.auto_panel.set_enemy_names(

            enemy_names,

            ignored_names,

        )


    def set_enemy_ignored(self, name, ignored):


        self.set_enemies_ignored([name], ignored)


    def set_enemies_ignored(self, names, ignored):


        unique_names = list({

            str(name).strip().casefold(): str(name).strip()

            for name in names

            if str(name).strip()

        }.values())


        for name in unique_names:


            self.entity_database.set_enemy_ignored(name, ignored)


        if unique_names:


            self.refresh_enemy_lists(force=True)









    # =====================================
    # GAME
    # =====================================


    def initialize_selected_game(self):


        selector = self.bot_tab.game_selector

        active_game = self.process_manager.get_active_game()

        game_id = active_game["id"] if active_game else selector.get_selected_game()

        if not game_id:

            selector.set_process_status(False, "Sin juegos")

            return


        selector.select_game(game_id)

        self.game_selected(game_id)


    def game_selected(self, game_id):


        if self.bot_engine.is_running():

            active_game = self.process_manager.get_active_game()

            if active_game:

                self.bot_tab.game_selector.select_game(active_game["id"])

            return


        previous_game = self.process_manager.get_active_game()

        previous_id = previous_game.get("id") if previous_game else None

        if not self.process_manager.set_game(game_id):

            self.bot_tab.game_selector.set_process_status(False, "Perfil inválido")

            return


        if previous_id != game_id:

            self.game_state_manager.invalidate_vision()


        self.detect_process()


    def detect_process(self):


        selector = self.bot_tab.game_selector

        game_id = selector.get_selected_game()

        if not game_id:

            selector.set_process_status(False, "Sin juegos")

            return


        active_game = self.process_manager.get_active_game()

        if not active_game or active_game.get("id") != game_id:

            if not self.process_manager.set_game(game_id):

                selector.set_process_status(False, "Perfil inválido")

                return


        selector.set_process_status(False, "Buscando...")

        if self.process_manager.find_process():

            details = (

                f"Proceso: {self.process_manager.get_name()}\n"

                f"PID: {self.process_manager.get_pid()}\n"

                f"Ventana: {self.process_manager.get_window_title()}"

            )

            selector.set_process_status(True, "Conectado", details)

            return


        messages = {

            "profile_incomplete": "Perfil incompleto",

            "window_not_found": "Ventana no encontrada",

            "process_mismatch": "Proceso no coincide",

        }

        selector.set_process_status(

            False,

            messages.get(self.process_manager.last_error, "No encontrado"),

        )


    def add_game(self):


        if self.bot_engine.is_running():

            return


        dialog = AddGameDialog(self.process_manager, self)

        if not dialog.exec():

            return


        data = dialog.get_game_data()

        game_id = self.game_profiles.create_game_id(data["name"])

        added = self.game_profiles.add_game(

            game_id,

            data["name"],

            data["process"],

            data["window"],

            data["width"],

            data["height"],

        )

        if not added:

            QMessageBox.warning(self, "No se pudo agregar", "El juego ya existe.")

            return


        self.bot_tab.game_selector.refresh(game_id)

        self.game_selected(game_id)


    def delete_game(self):


        if self.bot_engine.is_running():

            return


        selector = self.bot_tab.game_selector

        game_id = selector.get_selected_game()

        if not game_id:

            return


        answer = QMessageBox.question(

            self,

            "Eliminar juego",

            f'¿Eliminar "{selector.get_selected_name()}"?',

            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,

            QMessageBox.StandardButton.No,

        )

        if answer != QMessageBox.StandardButton.Yes:

            return


        if not self.game_profiles.remove_game(game_id):

            return


        games = self.game_profiles.get_games()

        if games:

            next_game_id = games[0]["id"]

            selector.refresh(next_game_id)

            self.game_selected(next_game_id)

        else:

            self.process_manager.clear_game()

            selector.refresh()











    # =====================================
    # BOT
    # =====================================


    def toggle_bot(self):


        if self.bot_engine.is_running():

            self.stop_bot()

        else:

            self.start_bot()











    def start_bot(self):


        if (
            not self.process_manager.is_connected()
            or not self.process_manager.has_window()
        ):

            return



        self.bot_engine.configure(

            self.bot_tab.auto_panel,

            self.bot_tab.rotation_panel,

            self.bot_tab.character_group,

        )


        self.bot_tab.lock_controls()

        self.bot_tab.game_selector.set_locked(True)



        self.bot_thread = QThread()


        self.bot_worker = BotWorker(

            self.bot_engine

        )


        self.bot_worker.moveToThread(

            self.bot_thread

        )


        self.stop_bot_requested.connect(

            self.bot_worker.stop

        )


        self.bot_worker.finished.connect(

            self.bot_thread.quit

        )


        self.bot_worker.error.connect(

            self.bot_start_failed

        )


        self.bot_worker.finished.connect(

            self.bot_worker.deleteLater

        )


        self.bot_thread.finished.connect(

            self.finish_bot_stop

        )


        self.bot_thread.finished.connect(

            self.bot_thread.deleteLater

        )


        self.bot_thread.started.connect(

            self.bot_worker.start

        )


        self.bot_thread.start()



        self.ui_timer.start()



        self.bot_tab.bot_controls.set_running()










    def stop_bot(self):


        self.ui_timer.stop()



        if not self.bot_worker:

            return


        self.bot_tab.bot_controls.start_button.setEnabled(False)

        self.stop_bot_requested.emit()



    def finish_bot_stop(self):


        self.ui_timer.stop()

        self.bot_worker = None

        self.bot_thread = None


        self.bot_tab.unlock_controls()

        self.bot_tab.game_selector.set_locked(False)

        self.bot_tab.bot_controls.set_stopped()

        self.bot_tab.bot_controls.start_button.setEnabled(True)

        if self._close_pending:

            self._close_pending = False

            self.close()


    def bot_start_failed(self, message):

        self.bot_tab.game_selector.set_process_status(

            False,

            "Error al iniciar",

            message,

        )










    # =====================================
    # POSITION
    # =====================================


    def refresh_player_position(self):

        self.bot_engine.refresh_player_position()


    def refresh_player_name(self):

        self.bot_engine.refresh_player_name()



    def lock_player_position(self):

        self.bot_engine.lock_player_position()



    def unlock_player_position(self):

        self.bot_engine.unlock_player_position()





    def update_character_ui(self):


        state = self.game_state_manager.get_state()



        self.bot_tab.character_group.update_state(

            state

        )


        self.bot_tab.target_group.update_state(

            state

        )


    def closeEvent(self, event):

        if self.bot_thread and self.bot_thread.isRunning():

            self._close_pending = True

            event.ignore()

            self.stop_bot()

            return

        self.bot_engine.input_manager.close()

        event.accept()
