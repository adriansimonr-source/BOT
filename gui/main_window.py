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


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.configure_window()

        # Managers
        self.process_manager = ProcessManager()

        self.create_menu()
        self.create_toolbar()
        self.create_central_widget()
        self.create_statusbar()

        self.connect_signals()

    def configure_window(self):

        self.setWindowTitle("Davion Automation Suite")
        self.resize(1200, 800)
        self.setMinimumSize(900, 550)

    def create_menu(self):

        menu = self.menuBar()

        menu.addMenu("Archivo")
        menu.addMenu("Configuración")
        menu.addMenu("Ayuda")

    def create_toolbar(self):

        toolbar = QToolBar()
        self.addToolBar(toolbar)

    def create_central_widget(self):

        central = QWidget()
        self.setCentralWidget(central)

        # Layout principal
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(20)

        # Panel izquierdo
        self.left_panel = LeftPanel()
        main_layout.addWidget(self.left_panel, 1)

        # Contenedor derecho
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

    def create_statusbar(self):

        status = QStatusBar()
        status.showMessage("Aplicación iniciada")
        self.setStatusBar(status)

    # ==================================================
    # Señales
    # ==================================================

    def connect_signals(self):

        self.left_panel.process_group.detect_process_button.clicked.connect(
            self.detect_process
        )

    # ==================================================
    # Detección del proceso
    # ==================================================

    def detect_process(self):

        self.left_panel.process_group.detecting()
        self.statusBar().showMessage("Buscando KathanaGame.exe...")

        if self.process_manager.find_process("KathanaGame.exe"):

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

            self.statusBar().showMessage("KathanaGame.exe no encontrado")