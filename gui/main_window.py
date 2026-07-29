from PySide6.QtWidgets import QLabel,QHBoxLayout,QToolBar,QVBoxLayout,QWidget,QMainWindow, QStatusBar
from PySide6.QtCore import Qt
from gui.left_panel import LeftPanel
from gui.right_panel import RightPanel

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.configure_window()

        self.create_menu()
        self.create_toolbar()
        self.create_central_widget()
        self.create_statusbar()

    def configure_window(self):

        self.setWindowTitle("Davion Automation suite")
        self.resize(1200,800)
        self.setMinimumSize(900,600)

    def create_menu(self):

        menu = self.menuBar()

        menu.addMenu("Archivo")
        menu.addMenu("Configuracion")
        menu.addMenu("Ayuda")

    def create_toolbar(self):

        toolbar = QToolBar()

        self.addToolBar(toolbar)

    def create_central_widget(self):

        central = QWidget()

        self.setCentralWidget(central)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        self.left_panel = LeftPanel()
        layout.addWidget(self.left_panel)
        self.right_panel = RightPanel()
        layout.addWidget(self.right_panel)

        central.setLayout(layout)

    def create_statusbar(self):

        status = QStatusBar()
        status.showMessage("Aplicacion iniciada")
        self.setStatusBar(status)