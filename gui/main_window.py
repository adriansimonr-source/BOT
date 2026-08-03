from PySide6.QtCore import (
    QThread,
    QTimer,
)

from PySide6.QtGui import QIcon

from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QTabWidget,
    QLabel,
)


from gui.tabs.bot_tab import BotTab
from gui.tabs.process_tab import ProcessTab


from core.process_manager import ProcessManager
from core.managers.game_state_manager import GameStateManager
from core.bot_engine import BotEngine
from core.bot_worker import BotWorker





class MainWindow(QMainWindow):


    def __init__(self):

        super().__init__()


        self.configure_window()

        self.apply_style()


        self.process_manager = ProcessManager()


        self.game_state_manager = GameStateManager(

            self.process_manager

        )


        self.bot_engine = BotEngine(

            self.game_state_manager

        )


        self.bot_thread = None

        self.bot_worker = None



        self.create_ui()

        self.create_timer()

        self.connect_signals()






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



        self.bot_tab = BotTab()

        self.process_tab = ProcessTab()

        self.log_tab = QLabel(

            "LOG"

        )



        self.tabs.addTab(

            self.bot_tab,

            "BOT"

        )


        self.tabs.addTab(

            self.process_tab,

            "PROCESO"

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

            100

        )


        self.ui_timer.timeout.connect(

            self.update_character_ui

        )









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


        self.process_tab.detect_button.clicked.connect(

            self.detect_process

        )


        self.bot_tab.character_group.refresh_position_button.clicked.connect(

            self.refresh_player_position

        )


        self.bot_tab.character_group.lock_position_button.clicked.connect(

            self.lock_player_position

        )


        self.bot_tab.character_group.unlock_position_button.clicked.connect(

            self.unlock_player_position

        )









    # =====================================
    # GAME
    # =====================================


    def game_selected(

        self,

        game_id

    ):


        self.process_manager.set_game(

            game_id

        )


        self.process_tab.set_game(

            self.bot_tab.game_selector.get_selected_name()

        )


        self.detect_process()











    # =====================================
    # PROCESS
    # =====================================


    def detect_process(self):


        if self.process_manager.find_process():


            self.process_tab.connected(

                self.process_manager.get_name(),

                self.process_manager.get_pid(),

                self.process_manager.get_window_title()

            )


        else:


            self.process_tab.disconnected()











    # =====================================
    # BOT
    # =====================================


    def toggle_bot(self):


        if self.bot_engine.is_running():

            self.stop_bot()

        else:

            self.start_bot()











    def start_bot(self):


        if not self.process_manager.is_connected():

            return



        self.bot_engine.configure(

            self.bot_tab.auto_panel,

            self.bot_tab.rotation_panel

        )


        self.bot_tab.lock_controls()



        self.bot_thread = QThread()


        self.bot_worker = BotWorker(

            self.bot_engine

        )


        self.bot_worker.moveToThread(

            self.bot_thread

        )


        self.bot_thread.started.connect(

            self.bot_worker.start

        )


        self.bot_thread.start()



        self.ui_timer.start()



        self.bot_tab.bot_controls.set_running()










    def stop_bot(self):


        self.ui_timer.stop()



        if self.bot_worker:

            self.bot_worker.stop()



        if self.bot_thread:

            self.bot_thread.quit()

            self.bot_thread.wait()



        self.bot_worker = None

        self.bot_thread = None



        self.bot_tab.unlock_controls()



        self.bot_tab.bot_controls.set_stopped()










    # =====================================
    # POSITION
    # =====================================


    def refresh_player_position(self):

        self.bot_engine.refresh_player_position()



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