from PySide6.QtCore import (
    Qt,
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
    apply_bot_config_requested = Signal(object)
    refresh_position_requested = Signal()
    lock_position_requested = Signal()
    unlock_position_requested = Signal()

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

        self._bot_stop_requested = False

        self.create_ui()

        self.create_timer()

        self.connect_signals()

        self.initialize_selected_game()

        self.refresh_enemy_lists(force=True)

    def configure_window(self):

        self.setWindowFlag(

            Qt.WindowType.WindowStaysOnTopHint,

            True

        )

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

    def connect_signals(self):

        self.bot_tab.bot_controls.start_button.clicked.connect(

            self.toggle_bot

        )

        self.bot_tab.configuration_changed.connect(

            self.queue_bot_configuration

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

        self.bot_tab.character_group.lock_position_button.clicked.connect(

            self.lock_player_position

        )

        self.bot_tab.character_group.unlock_position_button.clicked.connect(

            self.unlock_player_position

        )

        self.bot_tab.auto_panel.enemy_ignores_changed.connect(

            self.set_enemies_ignored

        )

        self.bot_tab.auto_panel.target_filters_save_requested.connect(

            self.save_target_filters

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

    def set_enemies_ignored(self, names, ignored):
        normalized_names = list({
            str(name).strip().casefold(): str(name).strip()
            for name in names
            if str(name).strip()
        }.values())
        set_batch = getattr(
            self.entity_database,
            "set_enemies_ignored",
            None,
        )
        if callable(set_batch):
            set_batch(normalized_names, ignored)
        else:
            for name in normalized_names:
                self.entity_database.set_enemy_ignored(name, ignored)
        if normalized_names:
            self.refresh_enemy_lists(force=True)

    def load_target_filters(self, game_id):
        filters = self.process_manager.config.get_game_target_filters(game_id)
        self.bot_tab.auto_panel.set_target_filters(
            filters["ignore_enabled"],
        )

    def save_target_filters(self, game_id=None):
        active_game = self.process_manager.get_active_game()
        game_id = game_id or (
            active_game.get("id") if active_game else None
        )
        if not game_id:
            return False

        panel = self.bot_tab.auto_panel
        state = panel.get_target_filter_state()

        try:
            self.process_manager.config.set_game_target_filters(
                game_id,
                state["ignore_enabled"],
            )
        except OSError as error:
            QMessageBox.warning(
                self,
                "No se pudo guardar",
                f"No se guardaron los filtros de objetivos:\n{error}",
            )
            return False

        panel.mark_target_filters_saved()
        return True

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

        if self.bot_worker is not None:

            active_game = self.process_manager.get_active_game()

            if active_game:

                self.bot_tab.game_selector.select_game(active_game["id"])

            return

        previous_game = self.process_manager.get_active_game()

        previous_id = previous_game.get("id") if previous_game else None

        if (
            previous_id
            and previous_id != game_id
            and self.bot_tab.auto_panel.has_unsaved_target_filters()
        ):
            if not self.save_target_filters(previous_id):
                self.bot_tab.game_selector.select_game(previous_id)
                return

        if not self.process_manager.set_game(game_id):

            self.bot_tab.game_selector.set_process_status(False, "Perfil inválido")

            return

        if previous_id != game_id:

            self.game_state_manager.invalidate_vision()

        self.load_target_filters(game_id)

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

        if self.bot_worker is not None:

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

        if self.bot_worker is not None:

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

        self.process_manager.config.remove_game_target_filters(game_id)

        games = self.game_profiles.get_games()

        if games:

            next_game_id = games[0]["id"]

            selector.refresh(next_game_id)

            self.game_selected(next_game_id)

        else:

            self.process_manager.clear_game()

            selector.refresh()

    def toggle_bot(self):

        if self.bot_worker is not None:

            self.stop_bot()

        else:

            self.start_bot()

    def start_bot(self):

        if self.bot_worker is not None:

            return

        if (
            not self.process_manager.is_connected()
            or not self.process_manager.has_window()
        ):

            return

        if (
            self.bot_tab.auto_panel.has_unsaved_target_filters()
            and not self.save_target_filters()
        ):

            return

        initial_config = self.bot_tab.build_configuration()

        self.bot_tab.lock_controls()

        self.bot_thread = QThread()

        self.bot_worker = BotWorker(

            self.bot_engine,

            initial_config,

        )

        self.bot_worker.moveToThread(

            self.bot_thread

        )

        self.stop_bot_requested.connect(

            self.bot_worker.stop

        )

        self.apply_bot_config_requested.connect(

            self.bot_worker.apply_config,

            Qt.ConnectionType.QueuedConnection,

        )

        self.refresh_position_requested.connect(
            self.bot_worker.refresh_player_position,
            Qt.ConnectionType.QueuedConnection,
        )
        self.lock_position_requested.connect(
            self.bot_worker.lock_player_position,
            Qt.ConnectionType.QueuedConnection,
        )
        self.unlock_position_requested.connect(
            self.bot_worker.unlock_player_position,
            Qt.ConnectionType.QueuedConnection,
        )

        self.bot_worker.finished.connect(

            self.bot_thread.quit

        )

        self.bot_worker.started.connect(

            self.finish_bot_start

        )

        self.bot_worker.error.connect(

            self.bot_start_failed

        )

        self.bot_worker.config_error.connect(

            self.bot_configuration_failed

        )

        self.bot_worker.config_applied.connect(

            self.bot_configuration_applied

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

        self._bot_stop_requested = False

        self.bot_tab.bot_controls.set_starting()

    def finish_bot_start(self):

        if self.bot_worker is not None and not self._bot_stop_requested:

            self.bot_tab.bot_controls.set_running()

    def queue_bot_configuration(self, config):

        if self.bot_worker is not None:

            self.apply_bot_config_requested.emit(config)

    def stop_bot(self):

        self.ui_timer.stop()

        if not self.bot_worker:

            return

        self._bot_stop_requested = True

        self.bot_engine.request_stop()

        self.bot_tab.bot_controls.set_stopping()

        self.stop_bot_requested.emit()

    def finish_bot_stop(self):

        self.ui_timer.stop()

        self.bot_worker = None

        self.bot_thread = None

        self._bot_stop_requested = False

        self.bot_tab.unlock_controls()

        self.bot_tab.bot_controls.set_stopped()

        self.bot_tab.bot_controls.start_button.setEnabled(True)

        if self._close_pending:

            self._close_pending = False

            self.close()

    def bot_start_failed(self, message):

        if self.bot_worker is not None:

            self.bot_tab.bot_controls.set_stopping()

        self.bot_tab.game_selector.set_process_status(

            False,

            "Error del bot",

            message,

        )

    def bot_configuration_failed(self, message):

        self.bot_tab.game_selector.set_process_status(

            True,

            "Bot activo · revisar config",

            f"El último cambio produjo un error: {message}",

        )

    def bot_configuration_applied(self, _revision):

        if self.bot_worker is not None:

            self.bot_tab.game_selector.set_process_status(

                True,

                "Conectado",

            )

    def refresh_player_position(self):

        if self.bot_worker is not None:
            self.refresh_position_requested.emit()
        else:
            self.bot_engine.refresh_player_position()

    def lock_player_position(self):

        if self.bot_worker is not None:
            self.lock_position_requested.emit()
        else:
            self.bot_engine.lock_player_position()

    def unlock_player_position(self):

        if self.bot_worker is not None:
            self.unlock_position_requested.emit()
        else:
            self.bot_engine.unlock_player_position()

    def update_character_ui(self):

        state = self.game_state_manager.get_ui_state()

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

        if (
            self.bot_tab.auto_panel.has_unsaved_target_filters()
            and not self.save_target_filters()
        ):
            event.ignore()
            return

        self.bot_engine.input_manager.close()

        event.accept()
