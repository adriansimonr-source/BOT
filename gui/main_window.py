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


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.configure_window()

        self.create_menu()
        self.create_toolbar()
        self.create_central_widget()
        self.create_statusbar()

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