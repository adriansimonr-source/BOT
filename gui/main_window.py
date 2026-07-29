from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QHBoxLayout,
    QVBoxLayout,
)

from gui.left_panel import LeftPanel
from gui.right_panel import RightPanel
from gui.center_panel import CenterPanel

from core.process_manager import ProcessManager
from core.managers.game_state_manager import GameStateManager
from core.bot_engine import BotEngine


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.configure_window()

#Busca el proceso del juego y lo conecta al bot
        self.process_manager = ProcessManager()
        self.game_state_manager = GameStateManager(self.process_manager)
        self.bot_engine = BotEngine(self.game_state_manager)

#Qtimer para manteener el bucle del bot en ejecución
        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.bot_engine.update)
        self.timer.timeout.connect(self.update_character_ui)

        self.create_menu()
        self.create_toolbar()
        self.create_central_widget()
        self.create_statusbar()

        self.connect_signals()

#Configuración de la ventana principal

    def configure_window(self):

        self.setWindowTitle("Davion Automation Suite")
        self.resize(1200, 800)
        self.setMinimumSize(900, 550)

#Menu auxiliar para la ventana principal

    def create_menu(self):

        menu = self.menuBar()

        menu.addMenu("Archivo")
        menu.addMenu("Configuración")
        menu.addMenu("Ayuda")

#Toolbar auxiliar para la ventana principal

    def create_toolbar(self):

        toolbar = QToolBar()
        self.addToolBar(toolbar)

#Construccion de la GUI principal con los paneles izquierdo, derecho y central

    def create_central_widget(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)

        # Panel izquierdo
        self.left_panel = LeftPanel()
        main_layout.addWidget(self.left_panel, 1)

        # Panel derecho
        right_container = QWidget()

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.right_panel = RightPanel()
        self.center_panel = CenterPanel()

        right_layout.addWidget(self.right_panel)
        right_layout.addWidget(self.center_panel)
        right_layout.addStretch()

        right_container.setLayout(right_layout)

        main_layout.addWidget(right_container, 4)

        central.setLayout(main_layout)

#Barra de estado, es posible que la elimine en un futuro

    def create_statusbar(self):

        status = QStatusBar()
        status.showMessage("Aplicación iniciada")
        self.setStatusBar(status)

#Detectar proceso y conectar señales de los botones a las funciones correspondientes
    def connect_signals(self):

        self.left_panel.process_group.detect_process_button.clicked.connect(
            self.detect_process
        )

        self.left_panel.start_button.clicked.connect(
            self.toggle_bot
        )

# Detectar proceso
    def detect_process(self):

        self.left_panel.process_group.detecting()

        self.statusBar().showMessage(
            "Buscando proceso..."
        )

        found = self.process_manager.find_process(
            "KathanaGame.exe"
        )

        if found:

            self.left_panel.process_group.set_process(
                self.process_manager.get_name(),
                self.process_manager.get_pid()
            )

            self.left_panel.process_group.connected()

            self.left_panel.enable_start_button()

            self.statusBar().showMessage(
                f"Conectado a {self.process_manager.get_name()} (PID {self.process_manager.get_pid()})"
            )

        else:

            self.left_panel.process_group.clear_process()

            self.left_panel.process_group.disconnected()

            self.left_panel.disable_start_button()

            self.stop_bot()

            self.statusBar().showMessage(
                "Proceso no encontrado"
            )

# Bot start/stop logic

    def toggle_bot(self):

        if self.bot_engine.is_running():
            self.stop_bot()
        else:
            self.start_bot()

    def start_bot(self):

        if not self.process_manager.is_connected():
            return

        # Configurar todos los módulos
        self.bot_engine.configure(
            self.right_panel,
            self.center_panel
        )

        # Bloquear la interfaz
        self.right_panel.lock_controls()
        self.center_panel.lock_controls()

        # Iniciar motor
        self.bot_engine.start()

        # Iniciar Game Loop
        self.timer.start()

        # Actualizar interfaz
        self.left_panel.set_running()

        self.statusBar().showMessage(
            "Bot iniciado"
        )

    def stop_bot(self):

        # Detener Game Loop
        self.timer.stop()

        # Detener motor
        self.bot_engine.stop()

        # Desbloquear configuración
        self.right_panel.unlock_controls()
        self.center_panel.unlock_controls()

        # Actualizar interfaz
        self.left_panel.set_stopped()

        self.statusBar().showMessage(
            "Bot detenido"
        )

    def update_character_ui(self):
        state = self.game_state_manager.get_state()
        self.left_panel.character_group.update_state(state)