import sys

from core.runtime_paths import initialize_runtime_environment


def _verify_smoke_dependencies():
    import cv2
    import numpy
    import pytesseract

    from core.services.template_manager import TemplateManager

    if sys.platform == "win32":
        import win32api
        import win32gui
        import win32process
        from winrt.windows.graphics.capture import GraphicsCaptureSession

        GraphicsCaptureSession.is_supported()
    pytesseract.get_tesseract_version()
    if "eng" not in pytesseract.get_languages():
        raise RuntimeError("Tesseract no puede cargar el idioma eng")
    if not TemplateManager().list():
        raise RuntimeError("No se pudieron cargar los templates")


def main(argv=None):
    arguments = list(sys.argv if argv is None else argv)
    smoke_test = "--smoke-test" in arguments
    arguments = [arg for arg in arguments if arg != "--smoke-test"]

    initialize_runtime_environment()
    if smoke_test:
        _verify_smoke_dependencies()

    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from gui.main_window import MainWindow

    app = QApplication(arguments)
    window = MainWindow()
    window.show()
    if smoke_test:
        QTimer.singleShot(250, window.close)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
