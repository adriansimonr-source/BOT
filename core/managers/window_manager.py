import win32gui
import win32process


class WindowManager:
    MIN_WINDOW_WIDTH = 500
    MIN_WINDOW_HEIGHT = 300

    def __init__(self):
        self.hwnd = None

    def list_windows(self, title=None):
        """Return visible game-sized windows, optionally filtered by title."""
        matches = []
        title_filter = (title or "").strip().casefold()

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return

            window_title = win32gui.GetWindowText(hwnd).strip()
            if not window_title:
                return
            if title_filter and title_filter not in window_title.casefold():
                return

            try:
                rect = win32gui.GetWindowRect(hwnd)
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
            except win32gui.error:
                return

            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            if width < self.MIN_WINDOW_WIDTH or height < self.MIN_WINDOW_HEIGHT:
                return

            matches.append(
                {
                    "hwnd": hwnd,
                    "pid": pid,
                    "title": window_title,
                    "rect": rect,
                    "width": width,
                    "height": height,
                }
            )

        win32gui.EnumWindows(callback, None)
        return sorted(
            matches,
            key=lambda window: (
                window["title"].casefold(),
                window["pid"],
            ),
        )

    def find_window_by_title(self, title):
        windows = self.list_windows(title)
        self.hwnd = windows[0]["hwnd"] if windows else None
        return self.hwnd is not None

    def get_rect(self):
        if self.hwnd is None or not win32gui.IsWindow(self.hwnd):
            return None
        return win32gui.GetWindowRect(self.hwnd)

    def get_position(self):
        rect = self.get_rect()
        if rect is None:
            return None

        left, top, right, bottom = rect
        return {
            "x": left,
            "y": top,
            "width": right - left,
            "height": bottom - top,
        }

    def is_valid(self):
        return self.hwnd is not None and bool(win32gui.IsWindow(self.hwnd))
