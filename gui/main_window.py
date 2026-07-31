from PySide6.QtCore import QTimer

from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QTabWidget,
    QLabel,
)

from gui.tabs.bot_tab import BotTab
from gui.tabs.process_tab import ProcessTab

from core.process_manager import ProcessManager
from core.managers.game_state_manager import GameStateManager
from core.bot_engine import BotEngine



class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.configure_window()

        self.process_manager = ProcessManager()

        self.game_state_manager = GameStateManager(
            self.process_manager
        )

        self.bot_engine = BotEngine(
            self.game_state_manager
        )


        self.timer = QTimer(self)

        self.timer.setInterval(
            50
        )


        self.timer.timeout.connect(
            self.bot_engine.update
        )


        self.timer.timeout.connect(
            self.update_character_ui
        )


        self.create_menu()
        self.create_toolbar()
        self.create_central_widget()
        self.create_statusbar()

        self.connect_signals()



    def configure_window(self):

        self.setWindowTitle(
            "Davion Automation Suite"
        )

        self.resize(
            1200,
            800
        )



    def create_menu(self):

        menu = self.menuBar()

        menu.addMenu(
            "Archivo"
        )

        menu.addMenu(
            "Configuración"
        )

        menu.addMenu(
            "Ayuda"
        )



    def create_toolbar(self):

        self.addToolBar(
            QToolBar()
        )



    def create_central_widget(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )


        layout = QVBoxLayout()


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


        central.setLayout(
            layout
        )



    def create_statusbar(self):

        status = QStatusBar()

        status.showMessage(
            "Aplicación iniciada"
        )

        self.setStatusBar(
            status
        )



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



    def game_selected(
        self,
        game_id
    ):

        self.process_manager.set_game(
            game_id
        )


        name = (
            self.bot_tab.game_selector.get_selected_name()
        )


        self.process_tab.set_game(
            name
        )


        self.detect_process()



    def detect_process(self):

        found = self.process_manager.find_process()


        if found:


            self.process_tab.connected(
                self.process_manager.get_name(),
                self.process_manager.get_pid(),
                self.process_manager.get_window_title()
            )


            self.statusBar().showMessage(
                "Proceso conectado"
            )


        else:


            self.process_tab.disconnected()


            self.statusBar().showMessage(
                "Proceso no encontrado"
            )



    def toggle_bot(self):

        if self.bot_engine.is_running():

            self.stop_bot()

        else:

            self.start_bot()



    def start_bot(self):

        if not self.process_manager.is_connected():

            self.statusBar().showMessage(
                "Proceso no conectado"
            )

            return


        self.bot_engine.configure(
            self.bot_tab.auto_panel,
            self.bot_tab.rotation_panel
        )


        self.bot_tab.lock_controls()

        self.bot_engine.start()

        self.timer.start()


        self.bot_tab.bot_controls.set_running()



    def stop_bot(self):

        self.timer.stop()

        self.bot_engine.stop()

        self.bot_tab.unlock_controls()

        self.bot_tab.bot_controls.set_stopped()



    def update_character_ui(self):

        state = self.game_state_manager.get_state()


        self.bot_tab.character_group.update_state(
            state
        )


        self.bot_tab.target_group.update_state(
            state
        )